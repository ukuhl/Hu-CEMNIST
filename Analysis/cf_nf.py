import numpy as np
import torch
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from tqdm.auto import tqdm
from cel.datasets import FileDataset, MethodDataset
from cel.cf_methods import PPCEF, ExplanationResult
from cel.models import MaskedAutoregressiveFlow, MLPClassifier
from cel.losses import MulticlassDiscLoss
from sklearn.metrics import f1_score


class MyPPCEF(PPCEF):
    def explain(self, X: np.ndarray, y_origin: np.ndarray, y_target: np.ndarray,
                epochs: int = 1000, lr: float = 0.0005, **search_step_kwargs):
        # Wrap everything into a dataloader
        X_t = torch.FloatTensor(X)
        y_t = torch.LongTensor(y_origin)
        y_cf_t = torch.LongTensor(y_target)

        dataset = TensorDataset(X_t, y_t, y_cf_t)
        dataloader = DataLoader(dataset, batch_size=128)

        # Compute counterfactuals
        self.epochs = epochs
        self.gen_model.eval()
        for param in self.gen_model.parameters():
            param.requires_grad = False

        if self.disc_model:
            self.disc_model.eval()
            for param in self.disc_model.parameters():
                param.requires_grad = False

        deltas = []
        target_class = []
        original = []
        original_class = []
        for xs_origin, contexts_origin, contexts_target in dataloader:
            xs_origin = xs_origin.to(self.device)
            contexts_origin = contexts_origin.to(self.device)

            contexts_origin = contexts_origin.reshape(-1, 1)
            contexts_target = contexts_target.reshape(-1, 1)

            xs_origin = torch.as_tensor(xs_origin)
            xs_origin.requires_grad = False
            delta = torch.zeros_like(xs_origin, requires_grad=True)

            optimizer = optim.Adam([delta], lr=lr)
            loss_components_logging = {}

            for epoch in (epoch_pbar := tqdm(range(epochs))):
                search_step_kwargs["epoch"] = epoch
                optimizer.zero_grad()
                loss_components = self._search_step(
                    delta,
                    xs_origin,
                    contexts_origin,
                    contexts_target,
                    **search_step_kwargs,
                )
                mean_loss = loss_components["loss"].mean()
                mean_loss.backward()
                optimizer.step()

                for loss_name, loss in loss_components.items():
                    loss_components_logging.setdefault(f"cf_search/{loss_name}", []).append(
                        loss.mean().detach().cpu().item()
                    )

                disc_loss = loss_components["loss_disc"].detach().cpu().mean().item()
                prob_loss = loss_components["max_inner"].detach().cpu().mean().item()
                epoch_pbar.set_description(
                    f"Discriminator loss: {disc_loss:.4f}, Prob loss: {prob_loss:.4f}"
                )
                # if disc_loss < patience_eps and prob_loss < patience_eps:
                #     break

            deltas.append(delta.detach().cpu().numpy())
            original.append(xs_origin.detach().cpu().numpy())
            original_class.append(contexts_origin.detach().cpu().numpy())
            target_class.append(contexts_target.detach().cpu().numpy())

        deltas = np.concatenate(deltas, axis=0)
        originals = np.concatenate(original, axis=0)
        original_classes = np.concatenate(original_class, axis=0)
        target_classes = np.concatenate(target_class, axis=0)
        x_cfs = originals + deltas

        return ExplanationResult(
            x_cfs=x_cfs,
            y_cf_targets=target_classes,
            x_origs=originals,
            y_origs=original_classes,
            logs=loss_components_logging,
        )


class NFexplainer():
    def __init__(self, X_train, y_train, X_test, y_test):
        self._disc_model = None
        self._gen_model = None
        self._log_prob_threshold = None
        self._cf_method = None

        self._fit_clf(X_train, y_train, X_test, y_test)

    def _fit_clf(self, X_train, y_train, X_test, y_test) -> None:
        # Prepare data
        X_train_t, X_test_t = torch.FloatTensor(X_train), torch.FloatTensor(X_test)
        y_train_t, y_test_t = torch.LongTensor(y_train), torch.LongTensor(y_test)

        train_loader = DataLoader(TensorDataset(X_train_t, y_train_t),
                                  batch_size=256, shuffle=True)

        test_loader = DataLoader(TensorDataset(X_test_t, y_test_t),
                                 batch_size=256, shuffle=False)

        # Train classifier
        self._disc_model = MLPClassifier(
            num_inputs=X_train.shape[1],
            num_targets=10,
            hidden_layer_sizes=[128],
        )
        self._disc_model.fit(train_loader, test_loader, epochs=50, patience=3, lr=1e-3)
        y_test_pred = self._disc_model.predict(X_test)
        print(f"F1-score: {f1_score(y_test, y_test_pred, average='weighted')}")

        # Fit generator
        self._gen_model = MaskedAutoregressiveFlow(
            features=X_train.shape[1],
            hidden_features=8,
            context_features=1,
        )
        self._gen_model.fit(train_loader, test_loader, epochs=100)

        self._log_prob_threshold = torch.quantile(self._gen_model.predict_log_prob(test_loader), 0.25)
        self._cf_method = MyPPCEF(
            gen_model=self._gen_model,
            disc_model=self._disc_model,
            disc_model_criterion=MulticlassDiscLoss(),
        )

    def compute_counterfactual(self, x_orig: np.ndarray, y_orig: np.ndarray, y_cf: np.ndarray) -> np.ndarray:
        res = self._cf_method.explain(X=x_orig.reshape(1, -1),
                                      y_origin=y_orig.reshape(1, -1),
                                      y_target=y_cf.reshape(1, -1),
                                      log_prob_threshold=self._log_prob_threshold,
                                      alpha=100)

        return res.x_cfs

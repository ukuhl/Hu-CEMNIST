

digits = {
            0: "digit_0_best_SSIM_idx_13280_rescaled.png",
            1: "digit_1_best_SSIM_idx_22398_rescaled.png",
            2: "digit_2_best_SSIM_idx_52316_rescaled.png",
            3: "digit_3_best_SSIM_idx_21717_rescaled.png",
            4: "digit_4_best_SSIM_idx_47566_rescaled.png",
            5: "digit_5_best_SSIM_idx_5752_rescaled.png",
            6: "digit_6_best_SSIM_idx_3774_rescaled.png",
            7: "digit_7_best_SSIM_idx_66586_rescaled.png",
            8: "digit_8_best_SSIM_idx_51272_rescaled.png",
            9: "digit_9_best_SSIM_idx_60471_rescaled.png"
        }


if __name__ == "__main__":
    idx = 0
    for a in range(10):
        for b in range(10):
            if a == b:
                continue
            print(f'\u007b"id": {idx}, "img": "{digits[a]}", "label": "{a}", "target": "{b}"\u007d,')
            idx += 1

import os
import time
import random
import base64
from pathlib import Path
from PIL import Image, ImageOps
from dateutil import parser
from io import BytesIO
from copy import deepcopy
import matplotlib.pyplot as plt
import mysql.connector
import pandas as pd
import numpy as np
import json


database = ""	# TODO: Put your database and credentials here!
user_name = ""
user_pw = ""


class DataMgr():
    def __init__(self):
        self.__init_database()

    def __connect_to_database(self):
        return mysql.connector.connect(host="localhost", user=user_name, password=user_pw,
                                       database=database)

    def __init_database(self):
        try:
            db = self.__connect_to_database()
            db.cursor().execute("CREATE TABLE IF NOT EXISTS logs (timestamp TEXT, userId TEXT NOT NULL, prolificId TEXT NOT NULL, trials TEXT NOT NULL, data LONGTEXT)")
            db.commit()

            return True
        except Exception as ex:
            print(ex)
            return False

    def export(self, dir_out="", dir_img_out="imgs"):
        #  Get all results from the database
        db = self.__connect_to_database()
        cur = db.cursor()
        cur.execute("SELECT userId, trials, data, timestamp FROM logs")
        records = cur.fetchall()

        data_user = []
        data_reactiontimes = []
        data_survey = []
        data_demographics = []
        data_prolific = []

        data_trials = None
        with open("site/static/data_trials.json", "rt") as f_in:
            data_trials = json.load(f_in)["allTrials"]
        def get_trial_info(trial_id: int) -> dict:
            for trial in data_trials:
                if trial["id"] == trial_id:
                    return trial

        empty_users = []

        for row in records:
            is_invalid_user = False

            try:
                user_id = row[0]

                log_time = parser.parse(row[3]).timestamp()
                trials = json.loads(row[1])["trialsID"]

                data = None
                try:                
                    data = json.loads(row[2])
                except Exception:
                    is_invalid_user = True

                # surveyData.csv
                q_options_1 = ["Strongly disagree", "Disagree", "Neutral", "Agree", "Strongly agree"]
                q_options_2 = ["Yes", "No"]
                q_options = {2: q_options_1,
                             3: q_options_1,
                             4: q_options_1,
                             5: q_options_1,
                             6: q_options_2,
                             8: q_options_2}

                for i in range(2, 11):
                    r = {"userID": user_id, "itemNo": i, "responseNo": -1, "checked": -1,
                         "responseText": None, "responseTime": None}

                    try:
                        r["responseTime"] = data["logTime"]["questionaire"][i]

                        q_resp = data["logQuestionnaireResponses"][i]
                        if i in q_options:
                            r = deepcopy(r)
                            q_resp = q_resp.replace("\xa0", "")
                            response_id = q_options[i].index(q_resp)
                            for r_i in range(len(q_options[i])):
                                r = deepcopy(r)
                                r["responseNo"] = int(r_i + 1)
                                if r_i == response_id:
                                    r["checked"] = int(1)
                                else:
                                    r["checked"] = int(0)

                                data_survey.append(r)
                        else:
                            r["responseText"] = q_resp

                            data_survey.append(r)
                    except Exception:    
                        is_invalid_user = True

                # userInfo.csv
                r = {"userID": user_id, "comprehensionCheck1_Q1": data["logAttentionCheck1"][0], "comprehensionCheck1_Q2": data["logAttentionCheck1"][1],
                     "comprehensionCheck1_Q3": data["logAttentionCheck1"][2], "comprehensionCheck1_Q4": data["logAttentionCheck1"][3],
                     "comprehensionCheck1_passed": None, "comprehensionCheck1_Q1_repeat": None,
                     "comprehensionCheck1_Q2_repeat": None, "comprehensionCheck1_Q3_repeat": None, "comprehensionCheck1_Q4_repeat": None,
                     "comprehensionCheck2_passed": None,
                     "trial1_baseDigit": get_trial_info(trials[0])["label"], "trial1_targetDigit": get_trial_info(trials[0])["target"], "trial1_percChange": None,
                     "trial2_baseDigit": get_trial_info(trials[1])["label"], "trial2_targetDigit": get_trial_info(trials[1])["target"], "trial2_percChange": None,
                     "trial3_baseDigit": get_trial_info(trials[2])["label"], "trial3_targetDigit": get_trial_info(trials[2])["target"], "trial3_percChange": None}

                if "logAttentionCheck2" in data.keys():
                    r["comprehensionCheck1_passed"] = False
                    r["comprehensionCheck1_Q1_repeat"] = data["logAttentionCheck2"][0]
                    r["comprehensionCheck1_Q2_repeat"] = data["logAttentionCheck2"][1]
                    r["comprehensionCheck1_Q3_repeat"] = data["logAttentionCheck2"][2]
                    r["comprehensionCheck1_Q4_repeat"] = data["logAttentionCheck2"][3]

                if data["logTime"]["questionaire"] == []:
                    r["comprehensionCheck2_passed"] = False

                # Extract strokes and amount of change
                responses = []

                try:
                    trials_img_data = data["logTrialsResponses"]
                    for i in range(len(trials_img_data)):
                        imgs = trials_img_data[i]

                        trial_responses = []

                        # Load original img
                        f_original_img = os.path.join("site/static/target_images_SSIM", get_trial_info(trials[i])["img"])
                        with Image.open(f_original_img) as im:
                            im = ImageOps.grayscale(im) 
                            im = np.array(im)
                            im = im.reshape(im.shape[0], im.shape[1], 1)
                            trial_responses.append(im)

                        # Process user generated images.
                        for img in imgs:
                            with Image.open(BytesIO(base64.b64decode(img.replace("data:image/png;base64,", "")))) as im:
                                im = ImageOps.grayscale(im) 
                                im = np.array(im)
                                im = im.reshape(im.shape[0], im.shape[1], 1)
                                trial_responses.append(im)

                        responses.append(np.concatenate(trial_responses, axis=2))
                except Exception:
                    is_invalid_user = True

                def compute_amount_of_change(img_data):
                    original_img = img_data[:, :, 0].flatten()
                    final_img = img_data[:, :, -1].flatten()

                    score = 0
                    for i in range(len(final_img)):
                        if original_img[i] != final_img[i]:
                            score += 1

                    return score / len(final_img)

                trial_0 = None
                try:
                    trial_0 = responses[0]
                    r["trial1_percChange"] = compute_amount_of_change(trial_0)
                except Exception:
                    is_invalid_user = True

                trial_1 = None
                try:
                    trial_1 = responses[1]
                    r["trial2_percChange"] = compute_amount_of_change(trial_1)
                except Exception:
                    is_invalid_user = True

                trial_2 = None
                try:
                    trial_2 = responses[2]
                    r["trial3_percChange"] = compute_amount_of_change(trial_2)
                except Exception:
                    is_invalid_user = True

                data_user.append(r)

                f_out = os.path.join(dir_out, dir_img_out, f"{user_id}.npz")
                Path(Path(f_out).parent).mkdir(parents=True, exist_ok=True)
                np.savez(f_out, trial_0=trial_0, trial_1=trial_1, trial_2=trial_2)

                # reactionTimes.cvs
                r = {"userID": user_id, "time_ConsentPage": None, "time_Instruct1": None,
                     "time_Instruct2": None, "time_CompCheck": None, "time_Instruct1_repeat": None,
                     "time_Instruct2_repeat": None, "time_CompCheck_repeat": None,
                     "time_trial1": None, "time_trial2": None, "time_trial3": None}

                try:
                    r["time_ConsentPage"] = data["logTime"]["welcome"] / 1000.
                    r["time_Instruct1"] = data["logTime"]["briefing0"] / 1000.
                    r["time_Instruct2"] = data["logTime"]["briefing1"] / 1000.
                    r["time_CompCheck"] = data["logTime"]["attention1"] / 1000.
                    if "briefing0-pass2" in data["logTime"]:
                        r["time_Instruct1_repeat"] = data["logTime"]["briefing0-pass2"] / 1000.
                        r["time_Instruct2_repeat"] = data["logTime"]["briefing1-pass2"] / 1000.
                        r["time_CompCheck_repeat"] = data["logTime"]["attention2"] / 1000.
                except Exception:
                    is_invalid_user = True

                try:
                    r["time_trial1"] = data["logTime"]["trials"][0] / 1000.
                except Exception:
                    is_invalid_user = True

                try:
                    r["time_trial2"] = data["logTime"]["trials"][1] / 1000.
                except Exception:
                    is_invalid_user = True

                try:
                    r["time_trial3"] = data["logTime"]["trials"][2] / 1000.
                except Exception:
                    is_invalid_user = True

                data_reactiontimes.append(r)

                # prolificData.csv
                r = {"userID": user_id,
                     "prolificID": data["prolificID"],
                     "studyStart": data["logTime"]["startTime"] / 1000.,  # In seconds
                     "studyEnd": None}  # In seconds

                try:
                    r["studyEnd"] = data["logTime"]["startTime"] + data["logTime"]["totalTime"] / 1000.
                except Exception:
                    is_invalid_user = True

                data_prolific.append(r)

                # demographics.csv
                age_options = ["18-24y", "25-34y", "35-44y", "45-54y", "55-65y", "65y and older", "prefer not to say"]
                gender_options = ["male", "female", "non-binary", "transgender", "other", "prefer not to say"]

                r = {"userID": user_id,
                     "gender": None,
                     "age": None}

                try:
                    r["gender"] = gender_options.index(data["logQuestionnaireResponses"][1].replace("\xa0", "")) + 1
                    r["age"] = age_options.index(data["logQuestionnaireResponses"][0].replace("\xa0", "")) + 1
                except Exception:
                    is_invalid_user = True

                data_demographics.append(r)
            except Exception as ex:
                is_invalid_user = True

            if is_invalid_user is True:
                print(f"Incomplete user {user_id}")
                empty_users.append({"userID": user_id,
                                    "prolificID": data["prolificID"],
                                    "studyStart": log_time})

        pd.DataFrame(empty_users).to_csv(os.path.join(dir_out, "emptyUsers.csv"), index=False)
        pd.DataFrame(data_user).to_csv(os.path.join(dir_out, "userInfo.csv"), index=False)
        pd.DataFrame(data_survey).to_csv(os.path.join(dir_out, "surveyData.csv"), index=False)
        pd.DataFrame(data_reactiontimes).to_csv(os.path.join(dir_out, "reactionTimes.csv"), index=False)
        pd.DataFrame(data_prolific).to_csv(os.path.join(dir_out, "prolificData.csv"), index=False)
        pd.DataFrame(data_demographics).to_csv(os.path.join(dir_out, "demographics.csv"), index=False)

    def get_list_of_users_in_db(self):
        try:
            db = self.__connect_to_database()
            cur = db.cursor()
            cur.execute("SELECT DISTINCT userId FROM logs")
            user_ids = cur.fetchall()

            return user_ids
        except Exception as ex:
            print(ex)
            return None

    def register_user(self, user_id: str, prolific_id: str):
        try:
            all_trials_id = list(range(0, 90))
            new_trials_id = None

            # Get all trial IDs that have been already used
            all_trials_id_count = {i: 0 for i in all_trials_id}
            db = self.__connect_to_database()
            cur = db.cursor()
            cur.execute("SELECT trials FROM logs")
            records = cur.fetchall()
            for row in records:
                user_trials_id = json.loads(row[0])["trialsID"]
                for trial_id in user_trials_id:
                    all_trials_id_count[trial_id] += 1

            # Select trial IDs for new user
            blacklisted_trials = []
            possible_trial_id = []
            for trial_id, count in all_trials_id_count.items():
                if trial_id in blacklisted_trials:
                    continue

                if count < 50:
                    possible_trial_id.append(trial_id)

            new_trials_id = random.choices(possible_trial_id, k=3)

            # Check if prolific ID already exisits
            db = self.__connect_to_database()
            cur = db.cursor()
            cur.execute("SELECT prolificId FROM logs")
            records = cur.fetchall()
            for row in records:
                if row[0] == prolific_id:
                    return {
                        "success": False
                    }

            # Store and return trial IDs
            db = self.__connect_to_database()
            cur = db.cursor()
            cur.execute("INSERT INTO logs (userId, prolificId, trials) VALUES(%s,%s,%s)", (user_id,
                                                                                           prolific_id,
                                                                                           json.dumps({"trialsID": new_trials_id})))
            db.commit()

            return {
                "trialsID": new_trials_id,
                "success": True
            }
        except Exception as ex:
            print(ex)
            return None

    def store_data(self, user_id, data):
        try:
            db = self.__connect_to_database()
            db.cursor().execute("UPDATE logs SET timestamp = %s, data = %s WHERE userId = %s", (str(time.ctime(time.time())), json.dumps(data), str(user_id)))
            db.commit()

            return True
        except Exception as ex:
            print(ex)
            return False

"use strict";

class Api {
    api_url = "api/"
    data_url = "static/"

    getQuestionnaireData() {
        return new Promise(resolve => {
            fetch(`${this.data_url}data_questionnaire.json`, {
                method: "GET"
            })
            .then(r => r.json())
            .then(jsonData => {
                resolve(jsonData)
            })
            .catch((error) => {
                console.error(error);
                resolve(undefined);
            })
        });
    }

    getTrialsData() {
        return new Promise(resolve => {
            fetch(`${this.data_url}data_trials.json`, {
                method: "GET"
            })
            .then(r => r.json())
            .then(jsonData => {
                resolve(jsonData)
            })
            .catch((error) => {
                console.error(error);
                resolve(undefined);
            })
        });
    }

    registerUser(userId, prolificId) {
        return new Promise(resolve => {
            fetch(`${this.api_url}registerUser`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    "userId": userId,
                    "prolificId": prolificId
                })
            })
            .then(r => r.json())
            .then(jsonData => {
                resolve(jsonData)
            })
            .catch((error) => {
                console.error(error);

                resolve(false);
            });
        });
    }

    storeData(userId, data) {
        return new Promise(resolve => {
            fetch(`${this.api_url}dataStorage`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    "userId": userId,
                    "data": data
                })
            })
            .then(_ => {
                resolve(true)
            })
            .catch((error) => {
                console.error(error);

                resolve(false);
            });
        });
    }
}
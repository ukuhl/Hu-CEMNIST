"use strict";

window.onload = () => {
    function uuid() {
        return ("" + Math.random()).substring(2, 10);
    };

    function shuffleArray(array) {
        for (let i = array.length - 1; i > 0; i--) {
            var j = Math.floor(Math.random() * (i + 1));
            var temp = array[i];
            array[i] = array[j];
            array[j] = temp;
        }
    };

    var api = new Api();
    api.getQuestionnaireData().then(myQuestionnaireData => {
        // Process questionaire
        for(var i=0; i != myQuestionnaireData.questions.length; i++) {  // Make sure all options are equally spaced by appending blanks
            var options = myQuestionnaireData.questions[i].options;
            var o_length = [];
            for(var j=0; j != options.length; j++) {
                o_length.push(options[j].length);
            }
            var max_o_length = Math.max(...o_length);

            var my_options = [];
            for(var j=0; j != options.length; j++) {
                if(options[j].length < max_o_length) {
                    var nDiff = max_o_length - options[j].length;
                    var my_option = options[j];
                    for(var z=0; z != nDiff; z++) {
                        my_option = my_option.concat("\u00A0");
                    }
                    my_options.push(my_option);
                }
                else {
                    my_options.push(options[j]);
                }
            }

            myQuestionnaireData.questions[i].options = my_options;
        }

        var myQuestionnaireResponseData = [];
        for(var i=0; i < myQuestionnaireData.questions.length; i++) {
            myQuestionnaireResponseData.push(undefined);
        }

        let urlParams = new URLSearchParams(window.location.search);    // Parse Prolific ID
        var prolificID = undefined;
        if(urlParams.has("PROLIFIC_PID")) {
            prolificID = urlParams.get("PROLIFIC_PID");
            console.log(prolificID);
        }
        else{
            prolificID = "NA"
        }

        api.getTrialsData().then(myTrialData => {
            var allTrials = myTrialData["allTrials"];

            var myTrialsResponseData = [];
            var myTrialsResponseTime = [];
            for(var i=0; i < 3; i++) {
                myTrialsResponseData.push(undefined);
                myTrialsResponseTime.push(undefined);
            }

            // Create app
            new Vue({
                el: "#app",
                components: {
                    question: {
                        props: ['q'],
                        template: `
                            <div class="question">
                                <h5>{{q.desc}}</h5>
                                <b-form-radio-group :require=true :options="q.options" @change="(checked) => $emit('click-on-radio-button', checked)">
                                </b-form-radio-group>
                                <br><br>
                            </div>
                        `
                    },
                },
                data: {
                    abortStudy: false,
                    btnBrushVariant: "primary",
                    btnEraserVariant: "outline-secondary",
                    checkboxUserConsent: "not_accepted",
                    checkboxAgeConsent: "not_accepted",
                    checkboxAttentionQ1: "",
                    checkboxAttentionQ2: "",
                    checkboxAttentionQ3: "",
                    checkboxAttentionQ4: "",
                    videoOver: false,
                    questionnaireData: myQuestionnaireData.questions,
                    curQuestionId: 0,
                    curQuestion: myQuestionnaireData.questions[0],
                    questionFreeText: "",
                    selectedAttentionCheck: undefined,
                    paint: undefined,
                    imgChangePercentage: 0,
                    userId: uuid(),
                    prolificID: prolificID,
                    curTime: Date.now(),
                    trialsData: [undefined, undefined, undefined],
                    curTrialID: 0,
                    curTrialData: allTrials[0],
                    questionnairePageNextButtonDisabled: true,
                    logTime: {
                        "startTime": undefined,
                        "totalTime": undefined,
                        "welcome": undefined,
                        "briefing0": undefined,
                        "briefing1": undefined,
                        "briefing0-pass2": undefined,
                        "briefing1-pass2": undefined,
                        "attention1": undefined,
                        "attention2": undefined,
                        "questionaire": [],
                        "trials": myTrialsResponseTime
                    },
                    logAttentionCheck1: undefined,
                    logAttentionCheck2: undefined,
                    logQuestionnaireResponses: myQuestionnaireResponseData,
                    logTrialsResponses: myTrialsResponseData
                },
                computed: {
                    isAttentionCheckBtnDisabled() {
                      return this.abortStudy || this.checkboxAttentionQ1 == "" || this.checkboxAttentionQ2 == "" || this.checkboxAttentionQ3 == "" || this.checkboxAttentionQ4 == "";
                    }
                },
                methods: {
                    onclickBtnBrush() {
                        this.btnBrushVariant = "primary";
                        this.btnEraserVariant = "outline-secondary";
                    },
                    onclickBtnEraser() {
                        this.btnBrushVariant = "outline-secondary";
                        this.btnEraserVariant = "primary";
                    },
                    resetPaintBtns() {
                        this.btnBrushVariant = "primary";
                        this.btnEraserVariant = "outline-secondary";
                    },
                    finish() {
                        this.logTime["totalTime"] = Date.now() - this.logTime["startTime"];

                        return api.storeData(this.userId, {
                            "prolificID": prolificID,
                            "logTime": this.logTime,
                            "logQuestionnaireResponses": this.logQuestionnaireResponses,
                            "logTrialsResponses": this.logTrialsResponses,
                            "logAttentionCheck1": this.logAttentionCheck1,
                            "logAttentionCheck2": this.logAttentionCheck2,
                            "userAgent": window.navigator.userAgent,
                            "screen": {"width": screen.width, "height": screen.height,
                                "availWidth": screen.availWidth, "availHeight": screen.availHeight,
                                "colorDepth": screen.colorDepth, "pixelDepth": screen.pixelDepth,
                                "orientation": screen.orientation.type
                            }
                        });
                    },
                    resetTimer() {
                        this.curTime = Date.now();
                    },
                    getTimer() {
                        return Date.now() - this.curTime;
                    },
                    onClickQuestionnaireRadioButton(questionsId, questionAnswer) {
                        this.logQuestionnaireResponses[questionsId] = questionAnswer;

                        this.questionnairePageNextButtonDisabled = false;
                    },
                    onClickWelcomePageNext() {
                        this.logTime["welcome"] = this.getTimer();
                        this.resetTimer();

                        this.logTime["startTime"] = Date.now();

                        // Register user
                        api.registerUser(this.userId, this.prolificID).then(userTrialIDs => {
                            // Check if registration was successfull
                            if(userTrialIDs["success"] == false) {
                                this.$bvModal.msgBoxOk("We have already received one attempt to enter this study with your ProlificID. In this study, participation is limited to one attempt per person. If you have already completed the study fully, you will receive reimbursement shortly.  If you did not complete the study due to failed comprehension checks before, we kindly ask you to return your submission by closing the study window and select the red circular arrow to 'Return + cancel reward' on Prolific. Rest assured that participants returning their submission will receive partial reimbursement for their time via Prolific's bonus system. Thank you!");
                            }
                            else {
                                if (typeof document.documentElement.requestFullscreen !== "undefined") {
                                    document.documentElement.requestFullscreen();   // Switch to fullscreen mode
                                }

                                this.finish();  // Make sure not data is lost even if the study is aborted!

                                userTrialIDs = userTrialIDs["trialsID"];
                                for(var i=0; i != userTrialIDs.length; i++) {
                                    this.trialsData[i] = allTrials[userTrialIDs[i]];
                                }
                                this.curTrialData = this.trialsData[0];
    
                                document.getElementById("welcomePage").style.display = "none";
                                document.getElementById("briefingPage0").style.display = "inline";
    
                                document.getElementById("video_tutorial").addEventListener('ended', this.onVideoIsOver.bind(this), false);
                            }
                        });
                    },
                    onVideoIsOver() {
                        this.videoOver = true;
                    },
                    onClickBriefing0NextPage() {
                        if(this.logTime["briefing0"] == undefined) {
                            this.logTime["briefing0"] = this.getTimer();
                        }
                        else {
                            this.logTime["briefing0-pass2"] = this.getTimer();
                        }
                        this.resetTimer();

                        document.getElementById("briefingPage0").style.display = "none";
                        document.getElementById("briefingPage1").style.display = "inline";

                        // Start playing the video
                        document.getElementById("video_tutorial").play();
                        this.videoOver = false;
                    },
                    onClickBriefing1NextPage() {
                        if(this.logTime["briefing1"] == undefined) {
                            this.logTime["briefing1"] = this.getTimer();
                        }
                        else {
                            this.logTime["briefing1-pass2"] = this.getTimer();
                        }
                        this.resetTimer();

                        document.getElementById("briefingPage1").style.display = "none";
                        document.getElementById("attentionPage").style.display = "inline";
                    },
                    initPaint() {
                        var imgSrc = `hucemnist/static/target_images_SSIM/${this.curTrialData["img"]}`;

                        this.imgChangePercentage = 0;
                        if(this.paint == undefined) {
                            this.paint = new Paint();
                            this.paint.init(imgSrc, this.updatePaintImg.bind(this));
                        }
                        else {
                            this.paint.imgSrc = imgSrc;
                            this.paint.loadImage();
                            this.resetPaintBtns();
                            this.paint.onClickBrush();
                        }
                    },
                    updatePaintImg(score) {
                        this.imgChangePercentage = Math.round(score * 100);
                    },
                    onClickAtentionCheckNextPage() {
                        if(this.logTime["attention1"] == undefined) {
                            this.logTime["attention1"] = this.getTimer();
                            this.resetTimer();
                        }
                        else {
                            this.logTime["attention2"] = this.getTimer();
                            this.resetTimer(); 
                        }

                        if(this.logAttentionCheck1 == undefined) {
                            this.logAttentionCheck1 = [this.checkboxAttentionQ1, this.checkboxAttentionQ2, this.checkboxAttentionQ3, this.checkboxAttentionQ4]
                        }
                        else {
                            this.logAttentionCheck2 = [this.checkboxAttentionQ1, this.checkboxAttentionQ2, this.checkboxAttentionQ3, this.checkboxAttentionQ4]
                        }

                        // Check answers!
                        if(this.checkboxAttentionQ1 == "B" && this.checkboxAttentionQ2 == "C" && this.checkboxAttentionQ3 == "A" && this.checkboxAttentionQ4 == "D") {

                            document.getElementById("attentionPage").style.display = "none";
                            document.getElementById("trialPage").style.display = "inline";
    
                            this.initPaint();
                        }
                        else if(this.logTime["attention2"]) {
                            this.abortStudy = true;
                            if (typeof document.documentElement.requestFullscreen !== "undefined") {
                                document.exitFullscreen();  // Exit fullscreen mode
                            }

                            this.$bvModal.msgBoxOk("Unfortunately, one or multiple answers were incorrect yet again. Following Prolific’s Comprehension Check policy, you will not be able to move to the study. Of course, we will still reward you for your time and effort. Please click the button below to return to Prolific to claim partial reimbursement. Thank you!", {okTitle: 'Claim partial reimbursement'}).then(_ => {
                                window.location.replace("https://app.prolific.com/submissions/complete?cc=C18JEBBH");
                            });
                        }
                        else {
                            this.$bvModal.msgBoxOk("One or multiple answers were incorrect! Please re-read the instructions and watch the video again. If you fail a second time to answer these questions correctly, you will will not be able to move to the study.");

                            this.checkboxAttentionQ1 = "";
                            this.checkboxAttentionQ2 = "";
                            this.checkboxAttentionQ3 = "";
                            this.checkboxAttentionQ4 = "";

                            document.getElementById("attentionPage").style.display = "none";
                            document.getElementById("briefingPage0").style.display = "inline";
                        }
                    },
                    onClickTrialNextPage() {
                        // Store results
                        this.logTrialsResponses[this.curTrialID] = this.paint.getAllStrokes();
                        this.logTime["trials"][this.curTrialID] = this.getTimer();

                        this.finish();  // Make sure no data is lost even if the study is aborted!

                        this.resetTimer();

                        // Next            
                        this.curTrialID += 1;
                        if(this.curTrialID >= this.trialsData.length) {
                            document.getElementById("trialPage").style.display = "none";
                            document.getElementById("startQuestions").style.display = "inline";
                        }
                        else {
                            this.curTrialData = this.trialsData[this.curTrialID];

                            this.initPaint();
                        }
                    },
                    onClickStartQuestionsNextPage() {
                        document.getElementById("startQuestions").style.display = "none";
                        document.getElementById("questionnairePage").style.display = "inline";
                    },
                    onClickQuestionairNextPage() {
                        this.logTime["questionaire"].push(this.getTimer());
                        this.resetTimer();

                        if(this.questionFreeText != "") {
                            this.logQuestionnaireResponses[this.curQuestionId] = this.questionFreeText;
                        }

                        this.curQuestionId += 1;
                        this.questionFreeText = "";
                    
                        if(this.curQuestionId < this.questionnaireData.length) {
                            this.curQuestion = this.questionnaireData[this.curQuestionId];
                            if(this.curQuestion.options.length != 1) {
                                this.questionnairePageNextButtonDisabled = true;
                            }
                        }
                        else {
                            document.getElementById("questionnairePage").style.display = "none";
                            document.getElementById("dataTransmissionPage").style.display = "inline";

                            this.finish().then(_ => {
                                document.getElementById("dataTransmissionPage").style.display = "none";
                                document.getElementById("debriefingPage").style.display = "inline";
                            });
                        }
                    },
                    onClickDebriefingClose() {
                        if (typeof document.documentElement.requestFullscreen !== "undefined") {
                            document.exitFullscreen();  // Exit fullscreen mode
                        }
                        this.$bvModal.msgBoxOk("Thank you! You may close this window/tab now.");
                    }
                }
            });
        });
    });
}

import React, { useState, useEffect } from "react";
import TimeFormat from "hh-mm-ss";
import axios from "axios";
import { buildStyles, CircularProgressbarWithChildren } from "react-circular-progressbar";
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import PauseIcon from '@mui/icons-material/Pause';
import Fab from "@mui/material/Fab";
import Zoom from "@mui/material/Zoom";
import DeleteForeverIcon from '@mui/icons-material/DeleteForever';
import ReplayIcon from '@mui/icons-material/Replay';
import SkipNextIcon from '@mui/icons-material/SkipNext';
import VolumeUpIcon from '@mui/icons-material/VolumeUp';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import Slider from '@mui/material/Slider';

function App() {
    // const defaultFocusTime = 60 * 25 * 1000;
    const defaultNormalFocusTime = 5 * 1000;
    // const defaultShortBreakTime = 60 * 5 * 1000;
    const defaultShortBreakTime = 3 * 1000;
    // const defaultLongBreakTime = 60 * 20 * 1000;
    const defaultLongBreakTime = 4 * 1000;
    // const defaultGraceTime = 15 * 60 * 1000;
    const defaultNormalGraceTime = 8 * 1000;

    const [defaultFocusTime, setDefaultNormalFocusTime] = useState(defaultNormalFocusTime);
    const [defaultBreakTime, setDefaultBreakTime] = useState(defaultShortBreakTime);
    const [defaultGraceTime, setDefaultGraceTime] = useState(defaultNormalGraceTime);


    const [graceTimeGetRequest, setGraceTimeGetRequest] = useState(false);
    const [graceTimeGetRequestInterval, setGraceTimeGetRequestInterval] = useState();


    const [status, setStatus] = useState("Stay Focused");
    const [tasks, setTasks] = useState(["Add a Task"]);
    const [inputTask, setInputTask] = useState("");
    const [isStart, setIsStart] = useState(false);
    const [timerPercentage, setTimerPercentage] = useState(100);
    const [sessionCount, setSessionCount] = useState(-1);
    const [timeLeft, setTimeLeft] = React.useState(0);
    const timer = React.useRef({});

    const interval = 1000;

    const start = React.useCallback(
        (timeToCount, ttc) => {
            window.cancelAnimationFrame(timer.current.requestId);

            const newTimeToCount = ttc !== undefined ? ttc : timeToCount;
            timer.current.started = null;
            timer.current.lastInterval = null;
            timer.current.timeToCount = newTimeToCount;
            timer.current.requestId = window.requestAnimationFrame(run);

            setTimeLeft(newTimeToCount);
        },
        [],
    );

    const run = (ts) => {
        if (!timer.current.started) {
            timer.current.started = ts;
            timer.current.lastInterval = ts;
        }

        const localInterval = Math.min(interval, (timer.current.timeLeft || Infinity));
        if ((ts - timer.current.lastInterval) >= localInterval) {
            timer.current.lastInterval += localInterval;
            setTimeLeft((timeLeft) => {
                timer.current.timeLeft = timeLeft - localInterval;

                return timer.current.timeLeft;
            });
        }

        if (ts - timer.current.started < timer.current.timeToCount) {
            timer.current.requestId = window.requestAnimationFrame(run);
        } else {
            timer.current = {};
            setTimeLeft(0);
        }
    };

    const pause = React.useCallback(
        () => {
            window.cancelAnimationFrame(timer.current.requestId);
            timer.current.started = null;
            timer.current.lastInterval = null;
            timer.current.timeToCount = timer.current.timeLeft;
        },
        [],
    );

    const resume = React.useCallback(
        () => {
            if (!timer.current.started && timer.current.timeLeft > 0) {
                window.cancelAnimationFrame(timer.current.requestId);
                timer.current.requestId = window.requestAnimationFrame(run);
            }
        },
        [],
    );

    React.useEffect(() => {
        return () => window.cancelAnimationFrame(timer.current.requestId);
    }, []);

    useEffect(() => {
        start(defaultFocusTime);
    }, []);

    useEffect(() => {
        setTimeout(() => {
            if (status === "Stay Focused") {
                setTimerPercentage(timer.current.timeLeft / defaultFocusTime * 100);
            } else if (status === "Grace Time") {
                setTimerPercentage(timer.current.timeLeft / defaultGraceTime * 100);
            } else {
                setTimerPercentage(timer.current.timeLeft / defaultBreakTime * 100);
            }

            if (timer.current.timeLeft === undefined) {
                if (status === "Stay Focused") {
                    setGraceTimeGetRequest(true);
                    setStatus("Grace Time");
                    restart(defaultGraceTime);
                } else if (status === "Grace Time") {
                    setGraceTimeGetRequest(false);
                    setStatus("Break");
                    restart(defaultBreakTime);
                } else {
                    setStatus("Stay Focused");
                    restart(defaultFocusTime);
                }
            }
        }, 1000);
    }, [timer.current.timeLeft]);

    useEffect(() => {
        if (graceTimeGetRequest) {
            setGraceTimeGetRequestInterval(setInterval(() => {
                console.log("still here");
                axios.get("http://localhost:8080/api/v1/muse/eeg/is_attentive")
                    .then((res) => {
                        console.log(res, res.data.is_attentive);

                        if (res.data.is_attentive === false) {
                            setStatus("Break");
                            restart(defaultBreakTime);
                        }
                    })
                    .catch((err) => {
                        console.error(err);
                    });
            }, 1000));
        } else {
            clearInterval(graceTimeGetRequestInterval);
        }
    }, [graceTimeGetRequest]);

    // useEffect(() => {
    //     if (status === "Stay Focused") {
    //         if (sessionCount === 3) {
    //             setDefaultBreakTime(defaultLongBreakTime);

    //             setSessionCount(0);
    //         } else {
    //             setDefaultBreakTime(defaultBreakTime);

    //             setSessionCount((prev) => prev + 1);
    //         }
    //     }
    // }, [status]);

    const progressBarStyle = {
        pathTransitionDuration: 0.5,
        pathColor: "#0098f7",
        textColor: "#0098f7"
    };

    const progressBarTextStyle = {
        fontSize: "3rem",
        fontFamily: "Noto Sans"
    };

    const resetIconStyle = {
        cursor: "pointer"
    };

    const generateSliderMarks = [];

    for (let i = 1; i < 40; i++) {
        // generateSliderMarks
    }

    const sliderMarks = [
        {},
        {}
    ];

    function handleTaskDelete(index) {
        setTasks((prev) => {
            return prev.filter((task) => {
                return task !== prev[index];
            });
        });
    }

    function handleTaskInputChange(e) {
        const { value } = e.target;

        setInputTask(value);
    }

    function handleTaskSubmit(e) {
        e.preventDefault();

        setTasks((prev) => {
            return [...prev, inputTask];
        });

        setInputTask("");
    }

    const restart = React.useCallback((time) => {
        start(time);
    }, []);

    function handleStartClick(e) {
        setIsStart((prev) => {
            if (prev) {
                resume();
            }

            return !prev;
        });

        if (!isStart) {
            pause();
        }
    }

    function handleResetClick() {
        restart(defaultFocusTime);
    }

    return (
        <div className="container">
            <nav>

            </nav>

            <div className="progress-container">
                <CircularProgressbarWithChildren value={timerPercentage} className="progress" strokeWidth={3} styles={buildStyles(progressBarStyle)}>
                    <div className="progress-text" style={progressBarTextStyle}>
                        <h1>{TimeFormat.fromS(timeLeft / 1000, "mm:ss")}</h1>

                        <div className="status">
                            <p>{status}</p>
                        </div>
                    </div>
                </CircularProgressbarWithChildren>
            </div>

            <div className="list">
                <div className="task-container">
                    {tasks.map((task, index) => {
                        return (
                            <div key={index}>
                                <p>{task}</p>
                                <DeleteForeverIcon onClick={() => handleTaskDelete(index)} />
                            </div>
                        );
                    })}
                </div>

                <hr />

                <form className="input-container" onSubmit={handleTaskSubmit}>
                    <input type="text" placeholder="Task" required value={inputTask} onChange={handleTaskInputChange} />
                    <button type="submit">+</button>
                </form>
            </div>

            <div className="footer">
                <div className="session-count-container">
                    <p>{sessionCount}/4<span>Number of sessions completed</span></p>
                </div>

                <div className="button-control-container">
                    {
                        status === "Stay Focused"
                            ? <ReplayIcon fontSize="large" name="clickable" style={resetIconStyle} onClick={handleResetClick} />
                            : <ReplayIcon fontSize="large" name="unclickable" style={resetIconStyle} />
                    }

                    <Zoom in={true}>
                        <Fab onClick={handleStartClick}>
                            {isStart ? <PlayArrowIcon fontSize="large" /> : <PauseIcon fontSize="large" />}
                        </Fab>
                    </Zoom>

                    <SkipNextIcon fontSize="large" />
                    <VolumeUpIcon fontSize="large" />
                    <OpenInNewIcon fontSize="large" />
                </div>
            </div>
        </div>
    );
}

export default App;
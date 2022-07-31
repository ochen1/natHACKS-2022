import React, { useState, useEffect } from "react";
import TimeFormat from "hh-mm-ss";
import { buildStyles, CircularProgressbarWithChildren } from "react-circular-progressbar";
import PlayArrowOutlinedIcon from '@mui/icons-material/PlayArrowOutlined';
import PauseIcon from '@mui/icons-material/Pause';
import Fab from "@mui/material/Fab";
import Zoom from "@mui/material/Zoom";
import DeleteForeverIcon from '@mui/icons-material/DeleteForever';
import ReplayIcon from '@mui/icons-material/Replay';
import Replay from "@mui/icons-material/Replay";

function App() {
    // const defaultFocusTime = 60 * 25;
    const defaultFocusTime = 5 * 1000;
    // const defaultBreakTime = 60 * 5 * 1000;
    const defaultBreakTime = 60 * 1000;

    const [focusTime, setFocusTime] = useState(defaultFocusTime);
    const [restTime, setRestTime] = useState(defaultBreakTime);
    const [graceTime, setGraceTime] = useState({
        // count: 0,
        // time: 0, (make this count * 60 * 5 * 1000 dynamically)
        // count: 3,
        // time: 3 * 60 * 5 * 1000
        count: 1,
        time: 10 * 1000
    });
    // const [finishFocusTime, setFinishFocusTime] = useState(false);
    const [status, setStatus] = useState("Stay Focused");
    const [tasks, setTasks] = useState(["Add a Task"]);
    const [inputTask, setInputTask] = useState("");
    const [isStart, setIsStart] = useState(false);
    const [timerPercentage, setTimerPercentage] = useState(100);
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


            if (status === "Stay Focused") {
                if (graceTime.count > 0) {
                    setStatus("Grace Time");
                    // restart(graceTime.time);
                } else {
                    setStatus("Break");
                    // restart(defaultBreakTime);
                }
            } else {
                setStatus("Stay Focused");
                // restart(defaultFocusTime);
            }
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

    const reset = React.useCallback(
        () => {
            if (timer.current.timeLeft) {
                window.cancelAnimationFrame(timer.current.requestId);
                timer.current = {};
                setTimeLeft(0);
            }
        },
        [],
    );

    const actions = React.useMemo(
        () => ({ start, pause, resume, reset }),
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
            console.log(timer.current.timeLeft);

            if (status === "Stay Focused") {
                setTimerPercentage(timer.current.timeLeft / defaultFocusTime * 100);
            } else if (status === "Grace Time") {
                setTimerPercentage(timer.current.timeLeft / graceTime.time * 100);
            } else {
                setTimerPercentage(timer.current.timeLeft / defaultBreakTime * 100);
            }

            if (timer.current.timeLeft === undefined) {
                if (status === "Stay Focused") {
                    if (graceTime.count > 0) {
                        restart(graceTime.time);
                    } else {
                        restart(defaultBreakTime);
                    }
                } else if (status === "Grace Time") {
                    restart(defaultBreakTime);
                } else {
                    restart(defaultFocusTime);
                }
            }
        }, 1000);
    }, [timer.current.timeLeft]);

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
        setTimerPercentage(100);

        restart(defaultFocusTime);
    }

    return (
        <div className="container">
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
                <div className="grace-time-container">
                    <p>{graceTime.count}<span>Number of grace time sessions added</span></p>
                </div>

                <div className="button-control-container">
                    <Zoom in={true}>
                        <Fab onClick={handleStartClick}>
                            {isStart ? <PlayArrowOutlinedIcon fontSize="large" /> : <PauseIcon fontSize="large" />}
                        </Fab>
                    </Zoom>

                    <Zoom in={true}>
                        <ReplayIcon fontSize="large" name="reset" style={resetIconStyle} onClick={handleResetClick} />
                        {/* make it only clickable during "stay focused" moments */}
                    </Zoom>
                </div>
            </div>
        </div>
    );
}

export default App;
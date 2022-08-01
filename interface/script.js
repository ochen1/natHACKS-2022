var chart = new Chart("chart", {
    type: "line",
    data: {
        labels: [0],
        datasets: [
            {
                label: "Attention",
                data: [0],
                fill: false,
                borderColor: "rgba(89, 239, 254, 0.4)",
                backgroundColor: "transparent",
            },
            {
                label: "Alertness",
                data: [0],
                borderColor: "rgba(255, 0, 211, 0.4)",
                fill: false,
                backgroundColor: "transparent",
            },
            {
                label: "Long-Term Average",
                data: [0],
                borderColor: "rgba(0, 255, 65, 0.4)",
                fill: false,
                backgroundColor: "transparent",
            },
        ],
    },
    options: {
        responsive: false,
        title: {
            display: true,
            text: 'Average Attentiveness and Alertness',
            fontColor: 'rgba(255, 255, 255, 0.87)',
        },
        legend: {
            // Display a legend for the two datasets
            display: true,
            labels: {
                fontColor: 'rgba(255, 255, 255, 0.87)',
            },
        },
        animation: {
            duration: 1000,
        },
        scales: {
            xAxes: [
                {
                    display: false,
                },
            ],
            yAxes: [
                {
                    ticks: {
                        fontColor: 'rgba(255, 255, 255, 0.87)',
                        suggestedMin: 0,
                        suggestedMax: 1,
                        stepSize: 0.1,
                    }
                }
            ]
        },
        tooltips: {
            enabled: false,
        },
        hover: {
            mode: null,
        }
    },
});

function needle(chart) {
    var needleValue = chart.chart.config.data.datasets[0].needleValue;
    var dataTotal = chart.chart.config.data.datasets[0].data.reduce((a, b) => a + b, 0);
    var angle = Math.PI + (1 / dataTotal * needleValue * Math.PI);
    var ctx = chart.chart.ctx;
    var cw = chart.chart.canvas.offsetWidth;
    var ch = chart.chart.canvas.offsetHeight;
    var cx = cw / 2;
    var cy = ch - 15;

    ctx.translate(cx, cy);
    ctx.rotate(angle);
    ctx.beginPath();
    ctx.moveTo(0, -3);
    ctx.lineTo(ch - 10, 0);
    ctx.lineTo(0, 3);
    ctx.fillStyle = 'rgb(0, 0, 0)';
    ctx.fill();
    ctx.rotate(-angle);
    ctx.translate(-cx, -cy);
    ctx.beginPath();
    ctx.arc(cx, cy, 5, 0, Math.PI * 2);
    ctx.fill();
}

Chart.pluginService.register({
    afterDraw: needle
});

var speedometer = new Chart("speedometer", {
    type: "doughnut",
    options: {
        circumference: Math.PI,
        rotation: Math.PI,
        responsive: false,
    },
    data: {
        datasets: [
            {
                borderColor: "#00ff41",
                data: [500, 500, 500],
                needleValue: 580
            }
        ]
    }
});

const socket = new WebSocket(window.location.origin.replace(/^http/, 'ws') + "/ws");
socket.addEventListener('open', () => {
    console.log('Connected to server');
});

socket.addEventListener('message', (event) => {
    chart.data.labels.push(chart.data.labels[chart.data.labels.length - 1] + 1);
    let data = JSON.parse(event.data);
    data.forEach((value, index) => {
        chart.data.datasets[index].data.push(value);
    });
    if (chart.data.labels.length > 40) {
        data.forEach((value, index) => {
            chart.data.datasets[index].data.shift();
        });
        chart.data.labels.shift();
    }
    chart.update();
    speedometer.data.datasets[0].needleValue = 500 * data[2];
    speedometer.update();
    needle(speedometer);
});


function updateLayout() {
    const chart = document.getElementById("chart");
    chart.width = chart.getBoundingClientRect().width;
    chart.height = Math.floor(chart.getBoundingClientRect().height);
}

// window.addEventListener("resize", updateLayout);
// window.addEventListener("load", updateLayout);
// setInterval(updateLayout, 1000);
var chart = new Chart("chart", {
    type: "line",
    data: {
        labels: [0],
        datasets: [
            {
                data: [0],
                borderColor: "rgba(0, 255, 0, 0.4)",
                fill: false,
                backgroundColor: "transparent",
            },
            {
                data: [0],
                borderColor: "rgba(0, 0, 255, 0.4)",
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
            display: false,
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
        }
    },
});

const socket = new WebSocket(window.location.origin.replace(/^http/, 'ws') + "/ws");
socket.addEventListener('open', () => {
    console.log('Connected to server');
});

socket.addEventListener('message', (event) => {
    chart.data.labels.push(chart.data.labels[chart.data.labels.length - 1] + 1);
    chart.data.datasets[0].data.push(event.data.parse()[0]);
    chart.data.datasets[1].data.push(event.data.parse()[1]);
    if (chart.data.labels.length > 40) {
        chart.data.labels.shift();
        chart.data.datasets[0].data.shift();
        chart.data.datasets[1].data.shift();
    }
    chart.update();
});


function updateLayout() {
    const chart = document.getElementById("chart");
    chart.width = chart.getBoundingClientRect().width;
    chart.height = Math.floor(chart.getBoundingClientRect().height);
}

// window.addEventListener("resize", updateLayout);
// window.addEventListener("load", updateLayout);
// setInterval(updateLayout, 1000);
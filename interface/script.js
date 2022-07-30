var chart = new Chart("chart", {
    type: "line",
    data: {
        labels: [0],
        datasets: [
            {
                data: [0],
                borderColor: "white",
                fill: false,
                backgroundColor: "transparent",
            },
        ],
    },
    options: {
        title: {
            display: true,
            text: 'Custom Chart Title',
            fontColor: '#40f2f9',
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
                        fontColor: '#40f2f9',
                        min: 0,
                        max: 1,
                        stepSize: 0.1,
                    }
                }
            ]
        }
    },
});

const socket = io("https://localhost/");

socket.on("plot", (data) => {
    chart.data.labels.push(chart.data.labels[chart.data.labels.length - 1] + 1);
    chart.data.datasets[0].data.push(data.data);
    if (chart.data.labels.length > 100) {
        chart.data.labels.shift();
        chart.data.datasets[0].data.shift();
    }
    chart.update();
});

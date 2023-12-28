// Handle Graphql subscription
// https://www.apollographql.com/docs/react/data/subscriptions/
// Javascript code to handle the subscription
const GQL = {
  CONNECTION_INIT: 'connection_init',
  CONNECTION_ACK: 'connection_ack',
  CONNECTION_ERROR: 'connection_error',
  CONNECTION_KEEP_ALIVE: 'ka',
  START: 'start',
  STOP: 'stop',
  CONNECTION_TERMINATE: 'connection_terminate',
  DATA: 'data',
  ERROR: 'error',
  COMPLETE: 'complete'
}

var wsGraphQL = null;

function init() {
  // Create a WebSocket link:
  const wsLink = new WebSocket("ws://localhost:8000/graphql", "graphql-ws");

  // Handle the connection
  wsLink.addEventListener("open", () => {
    console.log("Connected to the WS server");
    wsLink.send(JSON.stringify({
        type: GQL.CONNECTION_INIT,
        payload: null
    }))

    wsGraphQL = wsLink;
  });

  // Handle the error
  wsLink.addEventListener("error", (error) => {
    console.log("Error connecting to the WS server", error);
  });

  // Handle messages received
  wsLink.onMessage = event => {
      const data = JSON.parse(event.data)
        switch (data.type) {
            case GQL.CONNECTION_ACK: {
              console.log('success')
              break
            }
            case GQL.CONNECTION_ERROR: {
              console.error(data.payload)
              break
            }
            case GQL.CONNECTION_KEEP_ALIVE: {
              break
            }
      }
  }
}

// On page load
window.addEventListener("load", init);

function refresh() {
    // Check if the websocket is connected
    if (wsGraphQL.readyState === WebSocket.OPEN) {
        wsGraphQL.send(JSON.stringify({
            type: GQL.START,
            id: "1",
            payload: {
                query: `subscription {
                    newScore(target: 2) {
                        id
                        name
                        score
                    }
                }`,
                variables: null
            }
        }))
    }

    // Handle the message received
    wsGraphQL.onmessage = event => {
        const data = JSON.parse(event.data)
        switch (data.type) {
            case GQL.DATA: {
                console.log(data.payload.data.newScore)
                onScoreChange(data.payload.data.newScore)
                break
            }
            case GQL.ERROR: {
                console.error(data.payload)
                break
            }
            case GQL.COMPLETE: {
                console.log('completed')
                break
            }
        }
    }
}

// On Data Change
function onScoreChange(scores) {
    // Select table body
    let tableBody = document.getElementById('table-body');

    // Clear the table
    tableBody.innerHTML = '';

    // Reader header
    let header = document.createElement('tr');
    header.innerHTML = '<th>Rank</th><th>Name</th><th>Score</th>';
    tableBody.appendChild(header);

    // Render the scores
    scores.forEach(score => {
        // Create a new row
        let row = document.createElement('tr');

        // Create a new cell for the rank
        let rankCell = document.createElement('td');
        rankCell.innerText = score.id;
        row.appendChild(rankCell);

        // Create a new cell for the name
        let nameCell = document.createElement('td');
        nameCell.innerText = score.name;
        row.appendChild(nameCell);

        // Create a new cell for the score
        let scoreCell = document.createElement('td');
        scoreCell.innerText = score.score;
        row.appendChild(scoreCell);

        // Append the row to the table body
        tableBody.appendChild(row);
    });


}
document.addEventListener('DOMContentLoaded', () => {
    initGraph();
    fetchGraph();
});

let cy;

function initGraph() {
    cy = cytoscape({
        container: document.getElementById('cy'),
        style: [
            {
                selector: 'node',
                style: {
                    'background-color': '#3b82f6',
                    'label': 'data(label)',
                    'color': '#f1f5f9',
                    'text-valign': 'center',
                    'text-halign': 'center',
                    'font-size': '10px',
                    'width': '60px',
                    'height': '60px',
                    'border-width': 2,
                    'border-color': '#1e293b'
                }
            },
            {
                selector: 'node[type="literal"]',
                style: {
                    'background-color': '#10b981',
                    'shape': 'round-rectangle',
                    'width': 'label',
                    'height': '30px',
                    'padding': '10px'
                }
            },
            {
                selector: 'edge',
                style: {
                    'width': 2,
                    'line-color': '#64748b',
                    'target-arrow-color': '#64748b',
                    'target-arrow-shape': 'triangle',
                    'curve-style': 'bezier',
                    'label': 'data(label)',
                    'font-size': '8px',
                    'color': '#94a3b8',
                    'text-rotation': 'autorotate',
                    'text-background-opacity': 1,
                    'text-background-color': '#0f172a',
                    'text-background-padding': '2px'
                }
            }
        ],
        layout: {
            name: 'cose',
            animate: true
        }
    });

    cy.on('tap', 'node', function (evt) {
        const node = evt.target;
        log(`Clicked node: ${node.id()} (${node.data('label')})`, 'info');
    });
}

async function fetchGraph() {
    log('Fetching graph data...', 'info');
    const mode = document.getElementById('view-mode').value;
    try {
        const response = await fetch(`/api/graph?mode=${mode}`);
        const data = await response.json();

        if (data.elements) {
            cy.elements().remove();
            cy.add(data.elements);

            const layout = cy.layout({
                name: 'cose',
                animate: true,
                animationDuration: 500
            });
            layout.run();

            updateStats(data.elements.nodes.length, data.elements.edges.length);
            log(`Graph updated: ${data.elements.nodes.length} nodes, ${data.elements.edges.length} edges`, 'success');
        } else {
            log('No graph data received', 'error');
        }
    } catch (error) {
        log(`Error fetching graph: ${error.message}`, 'error');
    }
}

async function runStep(endpoint) {
    const overlay = document.getElementById('loading-overlay');
    overlay.classList.remove('hidden');
    log(`Running ${endpoint}...`, 'info');

    try {
        const response = await fetch(`/api/${endpoint}`, { method: 'POST' });
        const result = await response.json();

        if (response.ok) {
            log(result.message, 'success');
            if (result.planner_log) {
                log(`Planner Output:\n${result.planner_log}`, 'info');
            }
            if (result.executor_logs) {
                log('Executor Results:', 'info');
                result.executor_logs.forEach(item => {
                    const icon = item.status === 'Success' ? '✅' : '❌';
                    log(`${icon} ${item.policy}: ${item.status}`, item.status === 'Success' ? 'success' : 'error');
                });
            }

            // Auto refresh graph
            fetchGraph();
        } else {
            log(`Step failed: ${result.message}`, 'error');
        }
    } catch (error) {
        log(`Network error: ${error.message}`, 'error');
    } finally {
        overlay.classList.add('hidden');
    }
}

function log(message, type = 'info') {
    const consoleBox = document.getElementById('console-output');
    const entry = document.createElement('div');
    entry.className = `log-entry ${type}`;
    entry.innerText = `> ${message}`;
    consoleBox.appendChild(entry);
    consoleBox.scrollTop = consoleBox.scrollHeight;
}

function updateStats(nodes, edges) {
    document.getElementById('node-count').innerText = `${nodes} Nodes`;
    document.getElementById('edge-count').innerText = `${edges} Edges`;
}

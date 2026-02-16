'''
Decision Tree Component for Streamlit Dashboard
Creates an interactive flow diagram showing all the routes tested in the project.
Uses streamlit-flow for interactive visualization.
Reads decision tree structure from CSV file.
'''

import pandas as pd
import os
from streamlit_flow.elements import StreamlitFlowNode, StreamlitFlowEdge
from streamlit_flow.state import StreamlitFlowState


def get_status_color(status):
    """Map status to color."""
    status_lower = status.lower().strip()
    if 'successful' in status_lower or 'final solution' in status_lower:
        return '#50C878'  # Green
    elif 'dead end' in status_lower:
        return '#FF6B6B'  # Red
    elif 'exploratory' in status_lower or 'retained' in status_lower:
        return '#FFD93D'  # Yellow
    elif 'rejected' in status_lower:
        return '#FFA500'  # Orange
    else:
        return '#E0E0E0'  # Gray (default)


def create_node_id(stage, decision_point, option):
    """Create a unique node ID from stage, decision point, and option."""
    # Clean strings for ID
    stage_str = str(stage).strip()
    dp_str = decision_point.strip().replace(' ', '_').replace('/', '_').replace('→', '_').replace('×', '_').replace('(', '').replace(')', '')
    opt_str = option.strip().replace(' ', '_').replace('/', '_').replace('→', '_').replace('×', '_').replace('(', '').replace(')', '')
    # Limit length to avoid issues
    dp_str = dp_str[:30]
    opt_str = opt_str[:30]
    return f"s{stage_str}_{dp_str}_{opt_str}"[:80]  # Limit total length


def create_decision_tree_state():
    """
    Create and return a StreamlitFlowState object representing the decision tree.
    Reads from CSV file and builds the tree structure.
    
    Returns:
        StreamlitFlowState: The decision tree flow state with nodes and edges
    """
    # Define colors
    color_start = '#4A90E2'  # Blue for start
    
    # Get the CSV file path (same directory as this file)
    csv_path = os.path.join(os.path.dirname(__file__), 'data/decisiontree.csv')
    
    # Verify file exists
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found at: {csv_path}")
    
    # Read CSV with error handling
    try:
        df = pd.read_csv(csv_path, encoding='utf-8')
    except pd.errors.EmptyDataError:
        # Try reading with different encoding
        df = pd.read_csv(csv_path, encoding='latin-1')
    
    # Verify we have data
    if df.empty:
        raise ValueError(f"CSV file is empty: {csv_path}")
    
    # Verify required columns exist
    required_columns = ['Stage', 'Decision Point', 'Option / Branch Tested', 'Status', 'Reason / Outcome']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"CSV file missing required columns: {missing_columns}")
    
    # Track nodes by stage
    nodes_by_stage = {}  # {stage: [(node_id, node_obj, status)]}
    node_objects = {}  # {node_id: node_obj} for quick lookup
    
    # First pass: create all nodes
    x_spacing = 350  # Horizontal spacing between stages
    y_spacing = 180  # Vertical spacing between nodes
    
    # Add start node
    start_node = StreamlitFlowNode(
        id='start',
        pos=(0, 0),
        data={'content': '**Project Start**<br/>Robot Adoption & Employment'},
        node_type='input',
        source_position='right',
        target_position='left',
        style={
            'background': color_start,
            'color': '#000000',
            'border': '2px solid #000000',
            'borderRadius': '10px',
            'padding': '10px',
            'fontSize': '12px',
            'fontWeight': 'bold',
            'width': 'auto',
            'height': 'auto',
            'minWidth': '180px',
            'textAlign': 'center'
        }
    )
    node_objects['start'] = start_node
    
    # Process CSV rows
    for idx, row in df.iterrows():
        stage = row['Stage']
        decision_point = row['Decision Point']
        option = row['Option / Branch Tested']
        status = row['Status']
        reason = row['Reason / Outcome']
        
        # Initialize stage tracking
        if stage not in nodes_by_stage:
            nodes_by_stage[stage] = []
        
        # Create node ID
        node_id = create_node_id(stage, decision_point, option)
        
        # Build content with markdown
        content_parts = [
            f"**Stage {stage}**",
            f"**{decision_point}**",
            f"{option}"
        ]
        if reason and pd.notna(reason) and str(reason).strip():
            reason_text = str(reason).strip()
            if len(reason_text) > 80:
                reason_text = reason_text[:77] + "..."
            content_parts.append(f"<br/><small style='font-size: 9px;'>{reason_text}</small>")
        
        content = "<br/>".join(content_parts)
        
        # Get color based on status
        node_color = get_status_color(status)
        
        # Determine node type
        is_final = status.lower().strip() == 'final solution'
        node_type = 'output' if is_final else 'default'
        
        # Calculate position
        x_position = stage * x_spacing
        # Y position: center nodes vertically, distribute evenly
        nodes_in_stage = len(nodes_by_stage[stage])
        total_nodes_in_stage = len(df[df['Stage'] == stage])
        y_position = (nodes_in_stage - total_nodes_in_stage / 2 + 0.5) * y_spacing
        
        # Create node
        node = StreamlitFlowNode(
            id=node_id,
            pos=(x_position, y_position),
            data={'content': content},
            node_type=node_type,
            source_position='right',
            target_position='left',
            style={
                'background': node_color,
                'color': '#000000',
                'border': '2px solid #000000',
                'borderRadius': '10px',
                'padding': '10px',
                'fontSize': '11px',
                'fontWeight': 'bold' if is_final else 'normal',
                'width': 'auto',
                'height': 'auto',
                'minWidth': '200px',
                'maxWidth': '280px',
                'textAlign': 'center'
            }
        )
        
        nodes_by_stage[stage].append((node_id, node, status))
        node_objects[node_id] = node
    
    # Second pass: create edges
    edges = []
    
    # Connect start to all stage 1 nodes
    if 1 in nodes_by_stage:
        for node_id, _, _ in nodes_by_stage[1]:
            edge = StreamlitFlowEdge(
                id=f"start-{node_id}",
                source='start',
                target=node_id,
                animated=False,
                marker_end={'type': 'arrowclosed'},
                style={
                    'strokeWidth': 2.5,
                    'stroke': '#333333'
                }
            )
            edges.append(edge)
    
    # Connect nodes between stages
    # Connect ALL nodes from previous stage to ALL nodes in current stage
    # This ensures Stage 1 connects to Stage 2, Stage 2 to Stage 3, etc.
    for stage in sorted(nodes_by_stage.keys()):
        if stage == 1:
            continue
        
        prev_stage = stage - 1
        if prev_stage not in nodes_by_stage:
            continue
        
        # Connect ALL nodes from previous stage to ALL nodes in current stage
        for prev_node_id, _, _ in nodes_by_stage[prev_stage]:
            for node_id, _, _ in nodes_by_stage[stage]:
                edge = StreamlitFlowEdge(
                    id=f"{prev_node_id}-{node_id}",
                    source=prev_node_id,
                    target=node_id,
                    animated=False,
                    marker_end={'type': 'arrowclosed'},
                    style={
                        'strokeWidth': 2.5,
                        'stroke': '#333333'
                    }
                )
                edges.append(edge)
    
    # Add timeline nodes at the bottom
    # Calculate timeline positions based on stage positions
    max_stage = max(nodes_by_stage.keys()) if nodes_by_stage else 13
    timeline_y = -400  # Position timeline below the main flow
    
    # Timeline dates: Dec 2025 to Feb 9, 2026
    timeline_dates = [
        ('Dec 2025', 0),
        ('Jan 2026', x_spacing * (max_stage / 2)),
        ('Feb 9, 2026', x_spacing * max_stage)
    ]
    
    timeline_nodes = []
    timeline_edges = []
    
    for i, (date_label, x_pos) in enumerate(timeline_dates):
        timeline_node = StreamlitFlowNode(
            id=f'timeline_{i}',
            pos=(x_pos, timeline_y),
            data={'content': f'**{date_label}**'},
            node_type='default',
            source_position='right',
            target_position='left',
            style={
                'background': '#E8E8E8',
                'color': '#000000',
                'border': '2px solid #666666',
                'borderRadius': '5px',
                'padding': '8px',
                'fontSize': '10px',
                'fontWeight': 'bold',
                'width': 'auto',
                'height': 'auto',
                'minWidth': '100px',
                'textAlign': 'center'
            }
        )
        timeline_nodes.append(timeline_node)
        
        # Connect timeline nodes
        if i > 0:
            prev_timeline_id = f'timeline_{i-1}'
            timeline_edge = StreamlitFlowEdge(
                id=f"{prev_timeline_id}-timeline_{i}",
                source=prev_timeline_id,
                target=f'timeline_{i}',
                animated=False,
                marker_end={'type': 'arrowclosed'},
                style={
                    'strokeWidth': 2,
                    'stroke': '#666666',
                    'strokeDasharray': '5,5'  # Dashed line for timeline
                }
            )
            timeline_edges.append(timeline_edge)
    
    # Collect all nodes (main flow + timeline)
    nodes = [start_node] + [node_obj for _, node_obj, _ in sum(nodes_by_stage.values(), [])] + timeline_nodes
    
    # Collect all edges (main flow + timeline)
    all_edges = edges + timeline_edges
    
    # Create and return the state
    state = StreamlitFlowState(nodes=nodes, edges=all_edges)
    return state

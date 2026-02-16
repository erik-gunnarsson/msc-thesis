'''
3D Vector Space Component for Streamlit Dashboard
Creates an interactive 3D vector space diagram showing the relationships between 
different schools of thought with regards to robotization and collective bargaining.
'''

import pandas as pd
import plotly.graph_objects as go
import os


def create_3d_vectorspace():
    """
    Create and return an interactive 3D plotly figure showing papers in vector space.
    
    Returns:
        plotly.graph_objects.Figure: Interactive 3D scatter plot
    """
    # Get the CSV file path (absolute path for reliability)
    base_dir = os.path.dirname(os.path.dirname(__file__))  # Go up from components/ to streamlit/
    csv_path = os.path.join(base_dir, 'data', 'vectorspace.csv')
    csv_path = os.path.abspath(csv_path)  # Make absolute
    
    # Verify file exists
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found at: {csv_path}")
    
    # Read CSV
    df = pd.read_csv(csv_path)
    
    # Verify required columns exist
    required_columns = ['paper', 'institutions', 'reallocation', 'distribution', 'school']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"CSV file missing required columns: {missing_columns}")
    
    # Get unique schools for color mapping
    schools = df['school'].unique()
    colors = [
        '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
        '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
        '#aec7e8', '#ffbb78', '#98df8a', '#ff9896', '#c5b0d5'
    ]
    school_colors = {school: colors[i % len(colors)] for i, school in enumerate(schools)}
    
    # Create 3D scatter plot
    fig = go.Figure()
    
    # Add scatter points for each school
    for school in schools:
        school_df = df[df['school'] == school]
        fig.add_trace(go.Scatter3d(
            x=school_df['institutions'],
            y=school_df['reallocation'],
            z=school_df['distribution'],
            mode='markers',
            name=school,
            text=school_df['paper'],
            marker=dict(
                size=10,
                color=school_colors[school],
                opacity=0.8,
                line=dict(
                    color='black',
                    width=1
                )
            ),
            hovertemplate='<b>%{text}</b><br>' +
                         'Institutions: %{x:.2f}<br>' +
                         'Reallocation: %{y:.2f}<br>' +
                         'Distribution: %{z:.2f}<br>' +
                         '<extra></extra>'
        ))
    
    # Highlight "This Thesis" paper
    thesis_df = df[df['paper'].str.contains('Andersson', na=False)]
    if not thesis_df.empty:
        fig.add_trace(go.Scatter3d(
            x=thesis_df['institutions'],
            y=thesis_df['reallocation'],
            z=thesis_df['distribution'],
            mode='markers',
            name='This Thesis',
            text=thesis_df['paper'],
            marker=dict(
                size=15,
                color='#FFD700',  # Gold color
                opacity=1.0,
                symbol='diamond',  # Diamond shape to highlight thesis
                line=dict(
                    color='black',
                    width=2
                )
            ),
            hovertemplate='<b>%{text}</b><br>' +
                         'Institutions: %{x:.2f}<br>' +
                         'Reallocation: %{y:.2f}<br>' +
                         'Distribution: %{z:.2f}<br>' +
                         '<extra></extra>'
        ))
    
    # Update layout
    fig.update_layout(
        title={
            'text': '3D Vector Space: Schools of Thought on Robotization & Collective Bargaining',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18}
        },
        scene=dict(
            xaxis_title='Institutions',
            yaxis_title='Reallocation',
            zaxis_title='Distribution',
            xaxis=dict(
                range=[-1, 1],
                backgroundcolor='rgb(230, 230, 230)',
                gridcolor='white',
                showbackground=True,
                zerolinecolor='white'
            ),
            yaxis=dict(
                range=[-1, 1],
                backgroundcolor='rgb(230, 230, 230)',
                gridcolor='white',
                showbackground=True,
                zerolinecolor='white'
            ),
            zaxis=dict(
                range=[-1, 1],
                backgroundcolor='rgb(230, 230, 230)',
                gridcolor='white',
                showbackground=True,
                zerolinecolor='white'
            ),
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.5),
                center=dict(x=0, y=0, z=0)
            )
        ),
        width=1000,
        height=800,
        margin=dict(l=0, r=0, b=0, t=50),
        legend=dict(
            x=1.02,
            y=1,
            xanchor='left',
            yanchor='top'
        )
    )
    
    return fig


def get_vectorspace_data():
    """
    Load and return the vectorspace data as a DataFrame.
    
    Returns:
        pandas.DataFrame: The vectorspace data
    """
    # Get the CSV file path (absolute path for reliability)
    base_dir = os.path.dirname(os.path.dirname(__file__))  # Go up from components/ to streamlit/
    csv_path = os.path.join(base_dir, 'data', 'vectorspace.csv')
    csv_path = os.path.abspath(csv_path)  # Make absolute
    
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found at: {csv_path}")
    
    return pd.read_csv(csv_path)

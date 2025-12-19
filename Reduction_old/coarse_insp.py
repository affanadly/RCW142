import numpy as np
import io
from astropy.io import ascii
from astropy.table import Table
import plotly.graph_objects as go
import dash
from dash import Dash, dcc, dash_table, html, Input, Output, State, callback_context

from argparse import ArgumentParser

def field2cube(rashift, decshift, chanlo, chanup, imsize, cellsize):
    vertices = [
        rashift - 0.5*imsize*cellsize, decshift - 0.5*imsize*cellsize, chanlo,
        rashift + 0.5*imsize*cellsize, decshift - 0.5*imsize*cellsize, chanlo,
        rashift + 0.5*imsize*cellsize, decshift + 0.5*imsize*cellsize, chanlo,  
        rashift - 0.5*imsize*cellsize, decshift + 0.5*imsize*cellsize, chanlo,
        rashift - 0.5*imsize*cellsize, decshift - 0.5*imsize*cellsize, chanup,
        rashift + 0.5*imsize*cellsize, decshift - 0.5*imsize*cellsize, chanup,
        rashift + 0.5*imsize*cellsize, decshift + 0.5*imsize*cellsize, chanup,
        rashift - 0.5*imsize*cellsize, decshift + 0.5*imsize*cellsize, chanup
    ]
    lines = [
        [0, 1], [1, 2], [2, 3], [3, 0],
        [4, 5], [5, 6], [6, 7], [7, 4],
        [0, 4], [1, 5], [2, 6], [3, 7]
    ]
    for line in lines:
        yield [vertices[line[0]*3], vertices[line[1]*3]], \
              [vertices[line[0]*3 + 1], vertices[line[1]*3 + 1]], \
              [vertices[line[0]*3 + 2], vertices[line[1]*3 + 2]]
              
if __name__ == '__main__':
    ps = ArgumentParser(description='Interactive coarse maser image inspection')
    ps.add_argument('filename', type=str, help='Filename of the coarse maser catalogue')
    ps.add_argument('-t', '--thres', type=float, default=0.0, help='Threshold based on RMS map')
    ps.add_argument('-f', '--field', type=str, default=None, help='Field file to load (optional)')
    args = ps.parse_args()
    
    coarse = Table.read(args.filename)
    coarse = coarse[coarse['flux'] > args.thres]
    
    fig = go.Figure(data=[
        go.Scatter3d(
            x=coarse['deltax'], y=coarse['deltay'], z=(coarse['bchan'] + coarse['echan'])/2,
            mode='markers',
            marker=dict(
                size=2.5,
                color=coarse['velocity'],
                colorscale='jet',
                colorbar=dict(title='Velocity (km/s)'),
            ),
            customdata=coarse[['bchan', 'echan', 'flux']],
            hovertemplate=(
                '<b>Δx</b>: %{x:.3f} arcsec<br>' + 
                '<b>Δy</b>: %{y:.3f} arcsec<br>' +
                '<b>Channel</b>: %{customdata[0]:d} - %{customdata[1]:d}<br>' +
                '<b>Velocity</b>: %{marker.color:.2f} km/s<br>' + 
                '<b>Flux</b>: %{customdata[2]:.2f} Jy<br>' +
                '<extra></extra>'
            )
        )
    ], layout=dict(
        margin=dict(l=5, r=5, b=15, t=15),
        scene=dict(
            xaxis_title=r'ΔRA (arcsec)',
            yaxis_title=r'ΔDEC (arcsec)',
            zaxis_title='Channel',
            yaxis_autorange='reversed',
        ),
        showlegend=False,
        uirevision='constant'
        )
    )
    
    header = ['rashift', 'decshift', 'bchan', 'echan', 'cellsize', 'imsize']
    if args.field is not None:
        fields = [dict(zip(header, row)) for row in Table.read(args.field, format='ascii')[header]]
    else:
        fields = []
    
    app = Dash(__name__)
    app.layout = html.Div(
        [
            html.Div(
                [
                    html.H1('Coarse Clean Components Inspection'),
                    html.P('Clean components catalogue: ' + args.filename, 
                        style={'height': '0.75vh'}
                    ),
                    html.P('Fields file: ' + (args.field if args.field is not None else 'None'),
                        style={'height': '0.75vh'}
                    ),
                    html.P('Threshold: ' + str(args.thres) + ' Jy',
                        style={'height': '0.75vh'}
                    ),
                ], 
            ), 
            dcc.Graph(
                figure=fig, 
                id='plot', 
                style={'width': '95vw','height': '50vh'}
            ),
            dash_table.DataTable(
                data=fields,
                columns=[{'name': i, 'id': i, 'type':'numeric'} for i in header],
                id='fields_table',
                editable=True,
                row_selectable='multi',
                row_deletable=True,
                page_size=5,
            ),
            html.Div(
                [
                    html.Button('Add Field', id='add-field', n_clicks=0),
                    html.Button('Select All', id='select-all', n_clicks=0),
                    html.Button('Deselect All', id='deselect-all', n_clicks=0),
                ],
            ),
            html.Div(
                [
                    html.Button('Export Fields', id='export-fields', n_clicks=0),
                    html.Button('Export Plot', id='export-plot', n_clicks=0),
                ],
            ),
            dcc.Store(id='fields', storage_type='memory'),
            dcc.Store(id='camera', storage_type='memory'),
            dcc.Download(id='download-fields'),
            dcc.Download(id='download-plot'),
        ],
    )

    @app.callback(
        Output('fields', 'data'),
        Input('fields_table', 'data')
    )
    def mimic_changes(data):
        # save changes into memory
        return data

    @app.callback(
        Output('fields_table', 'selected_rows'),
        Input('select-all', 'n_clicks'),
        Input('deselect-all', 'n_clicks'),
        State('fields_table', 'data')
    )
    def select(select_all, deselect_all, data):
        # select all or deselect all rows
        if callback_context.triggered_id == 'select-all':
            return list(range(len(data)))
        if callback_context.triggered_id == 'deselect-all':
            return []
        return dash.no_update

    @app.callback(
        Output('fields_table', 'data', allow_duplicate=True),
        Input('add-field', 'n_clicks'),
        State('fields_table', 'data'),
        prevent_initial_call=True
    )
    def update_table(add_field, data):
        # add new row to table
        if callback_context.triggered_id == 'add-field':
            data.append({col: '' for col in header})
        if data:
            return data
        return dash.no_update

    @app.callback(
        Output('plot', 'figure'),
        Input('fields_table', 'selected_rows'),
        Input('fields_table', 'data'),
        State('plot', 'figure'),
        State('camera', 'data'),
    )
    def update_plot(selected_rows, data, figure, camera):
        # update plot
        figure['data'] = [figure['data'][0]] 
        if selected_rows:
            for row in selected_rows:
                field = data[row]
                if any(field[col] == '' for col in header):
                    continue
                try:
                    field['rashift'] = float(field['rashift'])
                    field['decshift'] = float(field['decshift'])
                    field['bchan'] = int(field['bchan'])
                    field['echan'] = int(field['echan'])
                except:
                    continue
                figure['data'] += [
                    go.Scatter3d(
                        x=x, y=y, z=z,
                        mode='lines',
                        line=dict(width=1, color='black'),
                        hoverinfo='none',
                        hovertemplate=(
                            f'<b>ΔRA</b>: {field["rashift"]} arcsec<br>' +
                            f'<b>ΔDec</b>: {field["decshift"]} arcsec<br>' +
                            f'<b>Channel</b>: {field["bchan"]} - {field["echan"]}<br>' +
                            '<extra></extra>'
                        )
                    )
                    for x, y, z in field2cube(
                        field['rashift'], field['decshift'], 
                        field['bchan'], field['echan'], 
                        field['imsize'], field['cellsize']
                    )]
        figure['layout']['scene']['camera'] = camera

        return figure

    @app.callback(
        Output('camera', 'data'),
        Input('plot', 'relayoutData')
    )
    def store_camera_position(relayoutData):
        # store camera position
        if relayoutData is not None:
            if 'scene.camera' in relayoutData:
                return relayoutData['scene.camera']
        return dash.no_update

    @app.callback(
        Output('download-fields', 'data'),
        Input('export-fields', 'n_clicks'),
        State('fields_table', 'data'),
        prevent_initial_call=True
    )
    def export_fields(export_fields, data):
        # export fields to txt file
        filtered_rows = []
        for row in data:
            if all(row[col] == '' for col in header):
                continue
            try:
                row['rashift'] = float(row['rashift'])
                row['decshift'] = float(row['decshift'])
                row['bchan'] = int(row['bchan'])
                row['echan'] = int(row['echan'])
            except:
                continue
            filtered_rows.append(row)
        filtered_rows = Table(filtered_rows)
        table_output = io.StringIO()
        ascii.write(filtered_rows, format='commented_header', output=table_output)
        return dict(content=table_output.getvalue(), filename='fields.txt')

    @app.callback(
        Output('download-plot', 'data'),
        Input('export-plot', 'n_clicks'),
        State('plot', 'figure'),
        prevent_initial_call=True
    )
    def export_plot(export_plot, figure):
        # export plot to html file
        plot_output = io.StringIO()
        fig = go.Figure(figure)
        fig.write_html(plot_output)
        return dict(content=plot_output.getvalue(), filename='plot.html')
    
    app.run_server()
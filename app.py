import dash
import pandas as pd
import plotly.express as px
import dash_bootstrap_components as dbc
from dash import callback,Output,Input,html,dcc,State
from dash.exceptions import PreventUpdate
from sqlalchemy import create_engine,text
from sqlalchemy.pool import NullPool
import io
import base64
from dash import dash_table

#color codes to be used for the application

#FFA500 -> orange
#FF6347 -> tomato

#instantiate our application
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY], suppress_callback_exceptions=True)

#make a connection to our databse
#its postgres running in docker
#we use NullPool instead of the default QueuePool
def make_connection():
     try:
         conn_string = "postgresql://root:root@172.24.0.2:5432/test"
         engine = create_engine(conn_string, poolclass=NullPool)
         connection = engine.connect()
     except Exception as e:
         print('sorry, a connection could not be made')
     return connection
     
#make a connection to the database
#we want to get the years
#they are unique:2017,2018,2019
connection = make_connection()
t = text(
    '''
    select
        extract(year from transaction_datetime) as years
    from test_data
    '''
)
df = pd.read_sql(t, con=connection)

#define the contents layout
content = html.Div([
    html.H4('Telcom Analytics Dashboard', style={'color':'#FF6347'}),
    html.Br(),
    
    #we begin creating our kpis
    dbc.Row([
        #total customers kpi
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4('Customers', style={'textAlign':'center'}),
                    html.P(id='customers',children=0, style={'textAlign':'center','color':'#FF6347'})
                ])
            ])
        ]),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4('Transactions', style={'textAlign':'center'}),
                    html.P(id='transactions',children=0, style={'textAlign':'center','color':'#FF6347'})
                ])
            ])
        ]),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4('Amount Sent', style={'textAlign':'center'}),
                    html.P(id='amount-sent',children=0, style={'textAlign':'center','color':'#FF6347'})
                ])
            ])
        ]),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4('Amount Received', style={'textAlign':'center'}),
                    html.P(id='amount-received',children=0, style={'textAlign':'center','color':'#FF6347'})
                ])
            ])
        ]),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4('Net Balance', style={'textAlign':'center'}),
                    html.P(id='net-balance',children=0, style={'textAlign':'center','color':'#FF6347'})
                ])
            ])
        ])
    ]),
    html.Br(),
    dbc.Row([
        dbc.Col([
            dcc.Graph(id='transactions-per-year')
        ], md=5, lg=5),
        dbc.Col([
            dcc.Graph(id='transactions-per-date')
        ], md=5, lg=7),
        
    ]),
    html.Br(),
    dbc.Row([
        dbc.Col([
            dcc.Graph(id='sent-amount-per-year')
        ], md=4,lg=4),
        dbc.Col([
            dcc.Graph(id='amount-received-per-year')
        ],md=4,lg=4),
        dbc.Col([
            dcc.Graph(id='net-balance-per-year')
        ],md=4,lg=4)
    ]),
    html.Br(),
    dbc.Row([
        dbc.Col([
            html.P('Total Amount Sent,Received And Net Balance Per Year', style={'textAlign':'center','color':'#FF6347','fontSize':'18px'}),
            html.Br(),
            dcc.Dropdown(id='years-un', options=[{'label': year,'value': year} for year in df['years'].unique()], placeholder='Select a year', style={
            'backgroundColor': 'rgba(0,0,0,0)',  # Transparent background
            'color': '#FF6347',  # Tomato color for text
            'border': '1px solid #FF6347',  # Tomato border
            #'borderRadius': '5px',  # Rounded corners
            #'padding': '10px',  # Padding inside the dropdown
            'fontSize': '16px',  # Font size
            'height': '40px',  # Height of the dropdown
            'width': '200px'   # Width of the dropdown
        }),
            html.Br(),
            dcc.Graph(id='sent-received-net-per-year')
        ])
    ]),
    html.Br(),
    dcc.Upload(
        id='upload-data',
        children=html.Div('Upload data'),
        multiple=False,
        style={
            'backgroundColor': '#FF6347',  # Orange background
            'color': 'white',  # White text color
            'border': '2px solid #FF6347',  # Orange border
            'borderRadius': '5px',  # Rounded corners
            'padding': '5px',  # Padding inside the button
            'fontSize': '18px',  # Font size
            'height': '40px',  # Short height
            'width': '150px',  # Width of the button
            'cursor': 'pointer',  # Pointer cursor
            #'textAlign': 'center',  # Center text
            #'display': 'inline-block',  # Inline block display
            #'lineHeight': '30px'  # Center text vertically
        }
    ),
    html.Br(),
    html.Div(id='upload-status'),
    html.Br(),
    html.Div(id='summary-stats'),
    html.Br(),
    html.Br(),
    dcc.Graph(id='data-visualization'),
])

#define the appliations layout
app.layout = html.Div([
   content,
   dcc.Interval(
        id='interval-component',
        interval=1*100000,  # Interval in milliseconds (1 second)
        n_intervals=0  # Number of intervals
    )
], style={'margin':'18px'})

#callback functions for our kpis
@callback(Output('customers','children'),
          Input('interval-component','n_intervals'))
def update_total_customers_kpi(n):
    if n is None:
        return PreventUpdate
    #make a connction to the db
    connection = make_connection()
    if connection is not None:
        t = text(
            '''
            select
                count(distinct customer_id) as total_customers
            from test_data
            '''
        )
        df = pd.read_sql(t, con=connection)
        if not  df.empty:
            total_customers = df['total_customers'].iloc[0]
        return total_customers
    
#callback function for all the transactions made
@callback(Output('transactions','children'),
          Input('interval-component','n_intervals'))
def update_total_transactions(n):
    if n is None:
        raise PreventUpdate
    #make a conn to the db
    connection = make_connection()
    if connection:
        t = text(
            '''
            select
                count(distinct transaction_id) as total_transactions
            from test_data
            '''
        )
        df = pd.read_sql(t, con=connection)
        if not df.empty:
            total_transactions = df['total_transactions']
        return total_transactions

#callback function for the  total amount received
@callback(Output('amount-sent','children'),
          Input('interval-component','n_intervals'))
def update_total_amount_sent(n):
    if n is None:
        return PreventUpdate
    #make a connection to the db
    connection = make_connection()
    if connection:
        t = text(
            '''
            select
                sum(sent_amount) as amount_sent
            from
                test_data
            where
                transaction_id in (select distinct transaction_id from test_data);

            '''
        )
        df = pd.read_sql(t, con=connection)
        if not df.empty:
            sent_amount = df['amount_sent'].iloc[0]
        return f" KSH {sent_amount:.1f}"
    
#callback function for the amount received kpi 
@callback(Output('amount-received','children'),
          Input('interval-component','n_intervals'))
def update_total_amount_received(n):
    if n is None:
        return PreventUpdate
    #make a connection to the db
    connection = make_connection()
    if connection:
        t = text(
            '''
            select
               sum(received_amount) as amount_received
            from test_data
            where
               transaction_id in (select distinct transaction_id from test_data)
            '''
        ) 
        df = pd.read_sql(t, con=connection)
        if not df.empty:
            amount_received = df['amount_received'].iloc[0]
        return f"KSH {amount_received:.1f}"

#callback function for the net balance
@callback(Output('net-balance','children'),
          Input('interval-component','n_intervals'))
def update_net_balance(n):
    if n is None:
        return PreventUpdate
    #make a conn to the db
    connection = make_connection()
    if connection:
        t = text(
            '''
            with net_balance as (
            select
                received_amount,
                balance_then,
                sent_amount,
                (received_amount + balance_then) - sent_amount as net_balance
            from test_data
            where transaction_id in (select distinct transaction_id from test_data)
            )
            select
                sum(net_balance) as net_balance
            from net_balance
            '''
        )
        df = pd.read_sql(t, con=connection)
        if not df.empty:
            net_balance = df['net_balance'].iloc[0]
        return f"KSH {net_balance:.1f}"

#callback function for transactions per year pie chart
@callback(Output('transactions-per-year','figure'),
          Input('interval-component','n_intervals'))
def plot_transactions_pie_chart(n):
    if n is None:
        return PreventUpdate
    #make a conn to the db
    connection = make_connection()
    if connection:
        t = text(
            '''
            select
                count(distinct transaction_id) as transactions,
	            extract(year from transaction_datetime) as year
            from test_data
            group by year
            '''
        )
        df = pd.read_sql(t, con=connection)
        if not df.empty:
             # Create the pie chart
            fig = px.pie(df, 
                         values='transactions', 
                         names='year', 
                         title='Transactions Per Year',
                         color_discrete_sequence=['#FFA500', '#FF6347'],  # Orange and Tomato colors
                         template='plotly_dark')

            # Customize layout for transparent background
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',  # Transparent background
                plot_bgcolor='rgba(0,0,0,0)',   # Transparent plot background
                title_font_color='#FF6347',
                legend_title_font_color='#FF6347',
                legend_font_color='#FF6347',
                font_color='#FF6347'
            )#FF6347
            return fig
        
#callback function for transactions per date bar chart
@callback(Output('transactions-per-date','figure'),
          Input('interval-component','n_intervals'))
def plot_transactions_bar_chart(n):
    if n is None:
        return PreventUpdate
    #make a con to the engine
    connection = make_connection()
    if connection:
        t = text(
            '''
            select
              count(distinct transaction_id) as transactions,
              date_trunc('day', transaction_datetime) as transaction_date
            from test_data
            group by date_trunc('day', transaction_datetime);
            '''
        )
        df = pd.read_sql(t, con=connection)
        if not df.empty:
           # Create the bar chart
            fig = px.bar(df, 
                         x='transaction_date', 
                         y='transactions', 
                         title='Transactions Per Date',
                         color='transactions',
                         color_discrete_sequence=['#FFA500', '#FF6347'],  # Tomato color
                         template='plotly_dark')

            # Customize layout for transparent background and tomato color
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',  # Transparent background
                plot_bgcolor='rgba(0,0,0,0)',   # Transparent plot background
                title_font_color='#FF6347',      # Tomato color for title
                xaxis_title_font_color='#FF6347', # Tomato color for x-axis title
                yaxis_title_font_color='#FF6347', # Tomato color for y-axis title
                xaxis_tickfont_color='#FF6347',  # Tomato color for x-axis ticks
                yaxis_tickfont_color='#FF6347',  # Tomato color for y-axis ticks
                font_color='#FF6347',            # Tomato color for general font
                xaxis=dict(showgrid=False),       # No grid lines on x-axis
                yaxis=dict(showgrid=False)        # No grid lines on y-axis
            )
            return fig


#callback function for total amount sent per year doughnut chart
@callback(Output('amount-received-per-year','figure'),
          Input('interval-component','n_intervals'))
def plot_received_amount_per_year_dchart(n):
    if n is None:
        raise PreventUpdate
    #make a conn to the database
    connection = make_connection()
    if connection:
        t = text(
            '''
            select
                sum(received_amount)as received,
            	extract(year from transaction_datetime) as year
            from test_data
            where transaction_id in (select distinct transaction_id from test_data)
            group by year       
            '''
        )
        df = pd.read_sql(t, con=connection)
        if not df.empty:
             # Create the doughnut chart
            fig = px.pie(df, 
                         values='received', 
                         names='year', 
                         title='Total Amount Received Per Year',
                         hole=0.6,  # Big hole in the center
                         color_discrete_sequence=['#FF6347'],  # Tomato color
                         template='plotly_dark')

            # Add the text "Received" inside the doughnut chart
            fig.update_layout(
                annotations=[dict(
                    text='Received',
                    x=0.5,
                    y=0.5,
                    font_size=20,
                    showarrow=False,
                    font_color='white'  # Tomato color
                )],
                paper_bgcolor='rgba(0,0,0,0)',  # Transparent background
                plot_bgcolor='rgba(0,0,0,0)',   # Transparent plot background
                title_font_color='#FF6347',      # Tomato color for title
                legend_title_font_color='#FF6347', # Tomato color for legend title
                legend_font_color='#FF6347',     # Tomato color for legend text
                font_color='#FF6347'             # Tomato color for general font
            )
            return fig
   
#callback function for the total sent amount doughnut chart per year
@callback(Output('sent-amount-per-year','figure'),
          Input('interval-component','n_intervals'))
def plot_total_sent_amount_per_year_dchart(n):
    if n is None:
        raise PreventUpdate
    #make a connection to the db
    connection = make_connection()
    if connection:
        t = text(
            '''
            select
               sum(sent_amount)as sent,
	           extract(year from transaction_datetime) as year
            from test_data
            where transaction_id in (select distinct transaction_id from test_data)
            group by year
            '''
        )
        df = pd.read_sql(t, con=connection)
        if not df.empty: 
             # Create the doughnut chart
            fig = px.pie(df, 
                         values='sent', 
                         names='year', 
                         title='Total Amount Sent Per Year',
                         hole=0.6,  # Big hole in the center
                         color_discrete_sequence=['#FF6347'],  # Tomato color
                         template='plotly_dark')

            # Add the text "Sent" inside the doughnut chart
            fig.update_layout(
                annotations=[dict(
                    text='Sent',
                    x=0.5,
                    y=0.5,
                    font_size=20,
                    showarrow=False,
                    font_color='white'  # Tomato color
                )],
                paper_bgcolor='rgba(0,0,0,0)',  # Transparent background
                plot_bgcolor='rgba(0,0,0,0)',   # Transparent plot background
                title_font_color='#FF6347',      # Tomato color for title
                legend_title_font_color='#FF6347', # Tomato color for legend title
                legend_font_color='#FF6347',     # Tomato color for legend text
                font_color='#FF6347'             # Tomato color for general font
            )
            return fig     

#callback function for the total net balance per year doughnut chart
@callback(Output('net-balance-per-year','figure'),
          Input('interval-component','n_intervals'))
def plot_total_net_balance_per_year_dchart(n):
    if n is None:
        raise PreventUpdate
    #make a connection to the db
    connection = make_connection()
    if connection:
        t = text(
            '''
            select
              sum((received_amount + balance_then) - sent_amount)as balance,
	          extract(year from transaction_datetime) as year
            from test_data
            where transaction_id in (select distinct transaction_id from test_data)
            group by year

            '''
        )
        df = pd.read_sql(t, con=connection)
        if not df.empty:
             # Create the doughnut chart
            fig = px.pie(df, 
                         values='balance', 
                         names='year', 
                         title='Total Net Balance Per Year',
                         hole=0.6,  # Big hole in the center
                         color_discrete_sequence=['#FF6347'],  # Tomato color
                         template='plotly_dark')

            # Add the text "Net Balance" inside the doughnut chart
            fig.update_layout(
                annotations=[dict(
                    text='Net Balance',
                    x=0.5,
                    y=0.5,
                    font_size=20,
                    showarrow=False,
                    font_color='white'  # Tomato color
                )],
                paper_bgcolor='rgba(0,0,0,0)',  # Transparent background
                plot_bgcolor='rgba(0,0,0,0)',   # Transparent plot background
                title_font_color='#FF6347',      # Tomato color for title
                legend_title_font_color='#FF6347', # Tomato color for legend title
                legend_font_color='#FF6347',     # Tomato color for legend text
                font_color='#FF6347'             # Tomato color for general font
            )
            return fig

#callback function for plotting amount received,amount sent,net balance
#this is foll all the years
#its a grouped bar chart
#once a user selects a year ,the chart is plotted automatically
@callback(Output('sent-received-net-per-year','figure'),
          [Input('interval-component','n_intervals'),
           Input('years-un','value')])
def plot_grouped_bar_chart(n, year):
    if n is None:
        raise PreventUpdate
    #make a conn to the db
    connection = make_connection()
    if connection:
        t = text(
            '''
            select
               sum(received_amount) as received,
               sum(sent_amount) as sent,
               sum((received_amount + balance_then) - sent_amount) as balance,
               extract(year from transaction_datetime) as years,
               extract(month from transaction_datetime) as month
            from test_data
            where transaction_id in (select distinct transaction_id from test_data)
            group by month,years
            order by month desc

            '''
        )
        df = pd.read_sql(t, con=connection)
        
        if not df.empty:
            if year:
                df = df[df['years'] == year]

            fig = px.bar(df, 
                         x='month', 
                         y=['received', 'sent', 'balance'], 
                         barmode='group', 
                         title='Amount Received, Sent, and Net Balance Per Month',
                         color_discrete_sequence=['#FF6347', '#FFA500', '#FF4500'],  # Tomato and similar colors
                         template='plotly_dark')

            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',  # Transparent background
                plot_bgcolor='rgba(0,0,0,0)',   # Transparent plot background
                title_font_color='#FF6347',      # Tomato color for title
                legend_title_font_color='#FF6347', # Tomato color for legend title
                legend_font_color='#FF6347',     # Tomato color for legend text
                font_color='#FF6347',            # Tomato color for general font
                xaxis=dict(showgrid=False),      # No grid lines
                yaxis=dict(showgrid=False)       # No grid lines
            )
            
            fig.update_traces(width=0.2)  # Make the bars narrower

            return fig


# Callback to handle file upload
@app.callback(
    [Output('upload-status', 'children'),
     Output('summary-stats', 'children'),
     Output('data-visualization', 'figure')],
    [Input('upload-data', 'contents')],
    [State('upload-data', 'filename')]
)
def upload_and_process_file(contents, filename):
    if contents is None:
        raise PreventUpdate
    
    # Decode and read the CSV file
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))

    # Perform transformations
    df['transaction_datetime'] = pd.to_datetime(df['transaction_datetime'])
    
  # #create engine
    engine = create_engine("postgresql://root:root@172.24.0.2:5432/test")
    # Load data to PostgreSQL
    df.to_sql('my_data', con=engine, if_exists='replace')

    # Create summary statistics
    summary = df.describe().to_dict()

    # Convert summary statistics to a string format
    summary_str = ''
    for col, stats in summary.items():
        summary_str += f"{col.capitalize()} Statistics:\n"
        for stat, value in stats.items():
            summary_str += f"{stat.capitalize()}: {value}\n"
        summary_str += "\n"

  # Generate first visualization (e.g., histogram)
    fig = px.histogram(df, x='transaction_datetime', title='Transactions over Time', template='plotly_dark')
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',  # Transparent background
        plot_bgcolor='rgba(0,0,0,0)',   # Transparent plot background
        title_font_color='#FF6347',      # Tomato color for title
        legend_title_font_color='#FF6347', # Tomato color for legend title
        legend_font_color='#FF6347',     # Tomato color for legend text
        font_color='#FF6347',            # Tomato color for general font
        xaxis=dict(showgrid=False),      # No grid lines
        yaxis=dict(showgrid=False)       # No grid lines
    )
    
    # Set color for bars from orange to tomato
    fig.update_traces(
        marker=dict(
            color='#FF6347',  # Tomato color for bars
        )
    )


    # Display a success message
    status = f'Data loaded and stored successfully.'

    # Return the results
    return status, html.Pre(summary_str), fig

            
#run application
if __name__ == "__main__":
    app.run_server(debug=True)

import csv 
import pandas as pd
from pathlib import Path
import dash  
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go  
import plotly.express as px
import pandas as pd 
import os   
import codecs
import argparse
import dash_bootstrap_components as dbc

parser = argparse.ArgumentParser() # 1.インスタンスの作成
parser.add_argument('--debug', action="store_true") # 2.必要なオプションを追加
args = parser.parse_args() # 3.オプションを解析


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

def convert_name(raw_name):
    year = raw_name[:4]
    month = raw_name[4:6]
    return f"{year}-{month}"

#ページが読み込まれたら行う処理
def serve_layout():
    #店名→分類のルールの読み込み
    rule = {}
    with open("ルール.csv") as f:
        reader = csv.reader(f)
        for row in reader:
            word = row[0]
            group = row[1]
            rule[word] = group
    #明細からカード使用情報の読み込み、家計簿のcsvを作成
    for meisai_csv in Path("明細").glob("*.csv"):
        output_csv = Path(f"家計簿/{convert_name(meisai_csv.stem)}.csv") 
        if output_csv.exists():
            continue
        table=[]
        with open(meisai_csv, encoding="cp932") as f:
            reader = csv.reader(f)
            total_value = 0
            inageya_value = 0
            for row in reader:
                if len(row) > 0 and "2021/" in row[0]:
                    date = row[0]
                    store_name = row[1][:-1]
                    value = int(row[4].replace(",",""))

                    group = "その他"
                    for word, group_name in rule.items():
                        if word in store_name:
                            group = group_name
                            break
                    table.append([date, store_name, group, value])
        with output_csv.open("w") as f:
            writer = csv.writer(f)
            writer.writerows(table)

    app = dash.Dash(__name__)
    cols = ["日付", "店名", "分類", "金額"]
    df_all = pd.DataFrame(index=[], columns=cols+["month"])
    children = []
    #　家計簿のcsvを読み込んで円グラフを作成
    for kakeibo_csv in sorted(Path("家計簿").glob("*.csv")):
        if kakeibo_csv.stem[0] == ".":
            continue
        with codecs.open(kakeibo_csv, 'r', 'utf-8', 'ignore') as f:
            df = pd.read_csv(f, header=None)
        df.columns=cols
        sum_value = df["金額"].sum()
        ## グラフの作成
        fig = px.pie(data_frame=df, values="金額", names="分類")
        ## 円グラフの表示設定
        fig.update_traces(hole=.4, textposition='inside', textinfo='percent+label+value', texttemplate="%{label}<br>¥%{value}<br>%{percent}")
        fig.update_layout(annotations=[dict(text=f"合計<br>¥{sum_value:,}", x=0.5, y=0.5, font_size=20, showarrow=False)])
        fig.update_layout(margin=dict(t=50, b=0, l=0, r=0), height=700)
        fig.update_layout(
            font=dict(
                size=20,
            )
        )
        ## 円グラフをタブに追加
        graph = dbc.Row(
            [
                dbc.Col(dcc.Graph(figure=fig), lg=6, md=12),
            ],
            justify="center",
        )
        tab = dcc.Tab(label=kakeibo_csv.stem, children=[graph])
        children.append(tab)
        ## 折れ線グラフ用にデータの追加
        df["月"] = kakeibo_csv.stem
        df_all = pd.concat([df_all, df])
    # 金額推移グラフ作成
    ## 各月の分類毎の金額合計を計算
    df_g = df_all.groupby(by=["月", "分類"], as_index=False).sum()
    ## 折れ線グラフを作成
    fig = px.line(df_g, x="月", y="金額", color='分類',markers=True)
    ## 折れ線グラフの表示設定
    fig.update_xaxes(dtick="M1", tickformat="%y年%m月")
    fig.update_layout(margin=dict(t=50, b=0, l=0, r=0), height=700)
    fig.update_layout(
        font=dict(
            size=20,
        )
    )
    fig.update_layout(yaxis_tickformat = 'f')
    fig.update_traces(
        line=dict(width=5.0),
        marker=dict(size=12),
    )
    ## 推移のタブ作成
    graph = dbc.Row(
        [
            dbc.Col(dcc.Graph(figure=fig), lg=10, md=12),
        ],
        justify="center",
    )
    tab = dcc.Tab(label="推移", children=[graph])
    children.append(tab)

    # タブの要素をreturn
    return html.Div([
        dbc.Row([
            dbc.Col(dcc.Tabs(children), width=12)
        ])
    ])

app.layout = serve_layout

if __name__ == '__main__':
    if args.debug:
        app.run_server(host="0.0.0.0", port=8055,debug=False)
    else:
        app.run_server(host="0.0.0.0", port=8050,debug=False)





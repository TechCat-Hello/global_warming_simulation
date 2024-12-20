from flask import Flask, request, render_template, send_file
import csv
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

app = Flask(__name__)

UPLOAD_FOLDER = 'static/files'  # 保存先ディレクトリ
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 気温上昇の計算関数
def calculate_temperature_rise(annual_emissions, years):
    x_values = np.arange(0, years + 1)
    cumulative_emissions = annual_emissions * x_values  # 年間排出量 × 経過年数で累積排出量を計算
    
    temperature_rise = (cumulative_emissions * 1.5) / 400
    return temperature_rise[-1], cumulative_emissions[-1]  # 最後の値を返す

    # AR6の単純比例計算: 400 Gtで1.5°C
    #reference_emissions = 400  # 残排出量 (Gt)
    #reference_temperature_rise = 1.5  # 上昇温度 (°C)
    
    
    temperature_rise = (cumulative_emissions * reference_temperature_rise) / reference_emissions
    return round(temperature_rise, 2), cumulative_emissions

# グラフの作成
def create_graph(annual_emissions, years):
    x_values = list(range(0, years + 1))  # 経過年数のリスト
    # 累積排出量に基づく温度上昇の計算式に変更
    y_values = [(annual_emissions * year * 1.5 / 400) for year in x_values]

    plt.figure()
    plt.plot(x_values, y_values, marker="o", linestyle="-", color="b", label="Temperature Rise")
    plt.title("Predicted Temperature Rise Over Time")
    plt.xlabel("Years")
    plt.ylabel("Temperature Rise (°C)")
    plt.grid()
    plt.legend()

    graph_filename = 'temperature_rise_graph.png'
    graph_path = os.path.join(app.config['UPLOAD_FOLDER'], graph_filename)
    plt.savefig(graph_path)
    plt.close()

    return graph_filename

@app.route("/", methods=["GET", "POST"])
def index():
    temperature_change = None
    img_filename = None
    csv_filename = None
    excel_filename = None
    error_message = None  # エラーメッセージ用の変数を追加

    if request.method == "POST":
        try:
            # 入力値の取得
            annual_co2_emission = float(request.form["annual_co2"])
            years = int(request.form["years"])

            # 入力値が正の数かどうかをチェック
            if annual_co2_emission <= 0 or years <= 0:
                error_message = "CO₂排出量と経過年数は正の数でなければなりません。"
            else:
                # 気温上昇の計算
                temperature_change, cumulative_emissions = calculate_temperature_rise(
                    annual_co2_emission, years
                )

                # グラフの作成
                img_filename = create_graph(annual_co2_emission, years)

                # CSVファイルの作成
                csv_filename = 'co2_temperature_prediction.csv'
                csv_path = os.path.join(app.config['UPLOAD_FOLDER'], csv_filename)

                with open(csv_path, mode='w', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow(['Years', 'Cumulative Emissions (Gt)', 'Temperature Rise (°C)'])
                    writer.writerow([years, cumulative_emissions, temperature_change])

                # Excelファイルの作成
                excel_filename = 'co2_temperature_prediction.xlsx'
                excel_path = os.path.join(app.config['UPLOAD_FOLDER'], excel_filename)

                df = pd.DataFrame({
                    'Years': [years],
                    'Cumulative Emissions (Gt)': [cumulative_emissions],
                    'Temperature Rise (°C)': [temperature_change]
                })
                df.to_excel(excel_path, index=False)

        except ValueError:
            error_message = "無効な数値です。"  # 数値変換エラーの場合のメッセージ

    return render_template("index.html", temperature_change=temperature_change, 
                           img_filename=img_filename, csv_filename=csv_filename, excel_filename=excel_filename,
                           error_message=error_message)  # エラーメッセージもテンプレートに渡す

# CSVファイルのダウンロード
@app.route('/download_csv')
def download_csv():
    csv_filename = 'co2_temperature_prediction.csv'
    csv_path = os.path.join(app.config['UPLOAD_FOLDER'], csv_filename)
    return send_file(csv_path, as_attachment=True, mimetype='text/csv')

# Excelファイルのダウンロード
@app.route('/download_excel')
def download_excel():
    excel_filename = 'co2_temperature_prediction.xlsx'
    excel_path = os.path.join(app.config['UPLOAD_FOLDER'], excel_filename)
    return send_file(excel_path, as_attachment=True, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

if __name__ == "__main__":
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    # Render環境でのデバッグモードの制御
    #本番環境用
    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    app.run(host="0.0.0.0", port=5000, debug=debug_mode, use_reloader=False) 



# # 前處理

# 資料處理套件
import pandas as pd

# 讀取資料
df_combined = pd.read_excel(r"C:\Users\RYAN\OneDrive\桌面\Python\高管case\curb_weight_bigdata_without2022.xlsx") 

'''使機器自動辨別各資料間的關聯，再依可能較相關之資料群進行分群'''

# Kmeans套件
from sklearn.cluster import KMeans

def kmeans_(df):
    
    included = ['Engine Size(L)', 'Cylinders']
    X = df[included]

    model = KMeans(n_clusters = 5, n_init='auto', random_state=1)  # 預計分為5群，迭代次數由模型自行定義
    model.fit(X)  # 建立模型

    df['Cluster'] = model.labels_  #將分類結果加回df
    
    return df

# 將訓練資料進行分群，增加可學習特徵，以提高預測準確度
df_combined = kmeans_(df_combined)


# # Fold-Validation

import xgboost as xgb
import numpy as np
import statsmodels.api as sm  #學生化殘差

'''訓練'''  

best_params =  {'colsample_bytree': 0.8, 'learning_rate': 0.1, 'max_depth': 9, 'n_estimators': 100, 'subsample': 0.8}

def training(df, best_params):  
    global X, y
    X = df[['Engine Size(L)', 'Cylinders', 'Cluster', 'weight']]
    y = df['CO2 Emissions(g/km)']
    
    # 使用最佳超參數建立模型
    best_model = xgb.XGBRegressor(**best_params)

    # 使用最佳超參數對完整的資料進行訓練
    best_model.fit(X, y)

    # 使用最佳超參數對完整的資料進行訓練
    return best_model


best_model = training(df_combined, best_params)

# # 繪製學習曲線
import matplotlib.pyplot as plt
from sklearn.model_selection import learning_curve, KFold, cross_val_score

def plot_learning_curve_r2(estimator, title, X, y, ylim=None, cv=None, n_jobs=1, train_sizes=np.linspace(.1, 1.0, 5)):
    plt.figure()
    plt.title(title)
    if ylim is not None:
        plt.ylim(*ylim)
    plt.xlabel("Training examples")
    plt.ylabel("R^2")
    train_sizes, train_scores, test_scores = learning_curve(
        estimator, X, y, cv=cv, scoring='r2', n_jobs=n_jobs, train_sizes=train_sizes)
    train_scores_mean = np.mean(train_scores, axis=1)
    train_scores_std = np.std(train_scores, axis=1)
    test_scores_mean = np.mean(test_scores, axis=1)
    test_scores_std = np.std(test_scores, axis=1)
    plt.grid()

    plt.fill_between(train_sizes, train_scores_mean - train_scores_std,
                     train_scores_mean + train_scores_std, alpha=0.1, color="#8737ED")  # Purple color
    plt.fill_between(train_sizes, test_scores_mean - test_scores_std,
                     test_scores_mean + test_scores_std, alpha=0.1, color="#0091DA")  # Blue color
    plt.plot(train_sizes, train_scores_mean, 'o-', color="#8737ED",  # Purple color
             label="Training R^2")
    plt.plot(train_sizes, test_scores_mean, 'o-', color="#0091DA",  # Blue color
             label="Cross-validation R^2")
    
    plt.legend(loc="lower right")
    return plt


# 使用最佳模型進行學習曲線繪製
title_second_stage = "Learning Curves (XGBoost)"

# 初始化交叉驗證
cv = KFold(n_splits=5, shuffle=True, random_state=42)

# 計算交叉驗證分數
cv_scores = cross_val_score(best_model, X, y, cv=cv, scoring='r2')  # 使用R^2作為評估標準

# 輸出交叉驗證分數
print("Cross-Validation R^2 Scores:", cv_scores)
print("Mean of Cross-Validation R^2 Scores:", np.mean(cv_scores))

mae_scores = cross_val_score(best_model, X, y, cv=cv, scoring='neg_mean_absolute_error')
# 將分數取平均，並取其相反數
print('MAE:', -mae_scores.mean())

plot_learning_curve_r2(best_model, title_second_stage, X, y, cv=cv, ylim=(0.0, 1.01), n_jobs=1)

plt.show()


# # 正式Testing

'''使用者互動介面'''

import tkinter as tk
from tkinter import filedialog
import pandas as pd

class TickerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("碳排預測")
        self.root.geometry("800x800")

        self.current_page = 1
        self.xls = None
        self.file_path = None
        self.TOTAL = None  # 新增全域變數 TOTAL

        # 第一頁
        self.page1_label = tk.Label(root, text="請上傳Excel檔案")
        self.page1_label.pack(pady=20)

        self.upload_button = tk.Button(root, text="上傳檔案", command=self.upload_file)
        self.upload_button.pack(pady=10)

        # 第二頁
        self.page2_label = tk.Label(root, text="請設定上下限")

        # 新增使用者填寫方框
        self.total_label = tk.Label(root, text="目標淘汰數量:")
        self.total_label.pack(pady=5)
        self.total_entry = tk.Entry(root)
        self.total_entry.pack(pady=5)

        self.limits_entries = {}
        self.back_button = tk.Button(root, text="上一步", command=self.prev_page)

    def upload_file(self):
        self.file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx;*.xls")])
        global xls
        try:
            self.xls = pd.read_excel(self.file_path)
            xls = pd.ExcelFile(self.file_path)
            self.show_page2()
        except pd.errors.ParserError:
            self.show_error("error: 檔案格式錯誤")

    def show_page2(self):
        if self.xls is not None:
            self.page1_label.pack_forget()
            self.upload_button.pack_forget()

            self.page2_label.pack(pady=20)

            for key in ['SP', 'PK', 'SEAT', 'Lux', 'L', 'M', 'S']:
                frame = tk.Frame(self.root)
                frame.pack(pady=5)

                label_lower = tk.Label(frame, text=f"{key} 下限:")
                label_lower.pack(side=tk.LEFT)
                entry_lower = tk.Entry(frame)
                entry_lower.pack(side=tk.LEFT)
                self.limits_entries[f"{key}_lower"] = entry_lower

                label_upper = tk.Label(frame, text=f"{key} 上限:")
                label_upper.pack(side=tk.LEFT)
                entry_upper = tk.Entry(frame)
                entry_upper.pack(side=tk.LEFT)
                self.limits_entries[f"{key}_upper"] = entry_upper

            # 提交按鈕
            self.submit_button = tk.Button(self.root, text="提交", command=self.submit_limits)
            self.submit_button.pack(pady=10)

            self.current_page = 2
        else:
            self.show_error("請先上傳Excel檔案")

    def prev_page(self):
        self.page2_label.pack_forget()
        self.submit_button.pack_forget()  
        self.page1_label.pack(pady=20)
        self.upload_button.pack(pady=10)

    def submit_limits(self):
        # 條件判斷：每一個上限必須大於或等於下限
        global limits_values, TOTAL
        for key in ['SP', 'PK', 'SEAT', 'Lux', 'L', 'M', 'S']:
            upper_limit = float(self.limits_entries[f"{key}_upper"].get())
            lower_limit = float(self.limits_entries[f"{key}_lower"].get())
            if upper_limit < lower_limit:
                self.show_error(f"{key} 上限必須大於或等於下限")
                return

        # 新增將使用者填寫之數字傳到全域變數 TOTAL
        try:
            self.TOTAL = int(self.total_entry.get())
        except ValueError:
            self.show_error("目標淘汰數量應為整數")
            return
        
        TOTAL = self.TOTAL
        limits_values = {key: {'上限': self.limits_entries[f"{key}_upper"].get(),
                               '下限': self.limits_entries[f"{key}_lower"].get()} for key in ['SP', 'PK', 
                                                                                            'SEAT', 'Lux', 'L', 'M', 'S']}
        print("上下限:", limits_values)
        print("目標淘汰數量:", self.TOTAL)

        # 回傳 file_path
        self.root.destroy()

    def show_error(self, message):
        error_label = tk.Label(self.root, text=message, fg="red")
        error_label.pack(pady=10)

if __name__ == "__main__":
    root = tk.Tk()
    app = TickerApp(root)
    root.mainloop()


'''以2022年，分類好的資料進行testing'''

def input_preprocess(file_path):
    # 讀取excel
    sheets = xls.sheet_names

    # 基於 '資料集' 工作表創建一個新的 df
    df = pd.read_excel(xls, sheet_name='資料集')

    for sheet in ['Special Purpose', 'Pickup', '2-seater', '豪車', 'Large', 'Medium', 'Small']:
        # 將每個工作表的資料加入到 df 中，使用 1 和 0 表示是否在該工作表中
        df[sheet] = (df['Model'].isin(xls.parse(sheet)['Model'])).astype(int)
    
    return df

df_formal = input_preprocess(xls)

from sklearn.metrics import r2_score, mean_absolute_error

def predict_(df_formal, best_model):
    
    # 用 k-means 自動分群
    df_formal = kmeans_(df_formal)
    
    X_formal = df_formal[['Engine Size(L)', 'Cylinders', 'Cluster', 'weight']]
    y_formal = df_formal['CO2 Emissions(g/km)']

    # 最終資料集預測
    y_formal_pred = best_model.predict(X_formal)

    # 計算及輸出預測性能指標
    print(f"1. Test R^2: {r2_score(y_formal, y_formal_pred)}")
    print(f"2. Test MAE: {mean_absolute_error(y_formal, y_formal_pred)}")

    # 新增預測值欄位到 DataFrame
    df_formal['Predicted_CO2'] = y_formal_pred

    return df_formal

# 預測
df_formal = predict_(df_formal, best_model)


# # 線性規劃

from pulp import LpProblem, LpVariable, lpSum, LpMaximize, value

def LN(df, co2COL, pickCOL):
    # 將欄位名稱依序替換
    df.rename(columns={
        'Special Purpose': 'SP',
        'Pickup': 'PK',
        '2-seater': 'SEAT',
        '豪車': 'Lux',
        'Large': 'L',
        'Medium': 'M',
        'Small': 'S'
    }, inplace=True)
    
    # 創建 PuLP 線性規劃模型
    model = LpProblem(name="Maximize-CO2-Emissions", sense=LpMaximize)

    # 創建二元變數，表示每輛車是否被選中
    selection_vars = [LpVariable(f'Selection_{i}', cat='Binary') for i in range(len(df))]
    
    # 限制式: 每一種類所挑選數量的限制
    for key, limits in limits_values.items():
        indices = list(df.index[df[key] == 1])
        lower_limit = int(limits['下限'])
        upper_limit = int(limits['上限'])
        model += lpSum(selection_vars[i] for i in indices) >= lower_limit, f"{key} lower limit"
        model += lpSum(selection_vars[i] for i in indices) <= upper_limit, f"{key} upper limit"

    # 限制式: SP+PK+SEAT+L+M+S=TOTAL (淘汰TOTAL台)
    model += lpSum(selection_vars) == TOTAL, f"Total {TOTAL} vehicles"

    # 目標式: 最大化 CO2 排放量
    model += lpSum([df[co2COL][i] * selection_vars[i] for i in range(len(df))])

    # 解決模型
    model.solve()

    # 將選中的車輛標記到新的 'select' 欄位中
    df[pickCOL] = [round(value(var)) for var in selection_vars]
    
    # 回傳解
    global selected_totals
    selected_totals = {}
    for key in ['SP', 'PK', 'SEAT', 'Lux', 'L', 'M', 'S']:
        indices = list(df.index[df[key] == 1])
        selected_totals[key] = sum([round(value(selection_vars[i])) for i in indices])
    
    return df


df_formal = LN(df_formal, 'Predicted_CO2', 'select')

df_compare = input_preprocess('Final_split_data.xlsx')
df_compare = LN(df_compare, 'CO2 Emissions(g/km)', 'Eliminated')


# # testing之預測性能比較

'''將預測產出df與直接產出df匹配後合併'''
# 選擇用於匹配的欄位
matching_columns = ['Make', 'Model', 'Vehicle Class', 'Engine Size(L)', 'Cylinders', 'Transmission']

# 進行匹配
merged_df = pd.merge(df_compare, df_formal, how='inner', on=matching_columns)

from sklearn.metrics import confusion_matrix, precision_recall_fscore_support, classification_report

# 提取真實情況和預測情況的欄資料
y_true = merged_df['Eliminated']  
y_pred = merged_df['select']

'''# 混淆矩陣及分類報告
print("Confusion Matrix:\n", confusion_matrix(df_compare['Eliminated'], df_formal['select']))  # 後為預測
print("\nClassification Report:\n", classification_report(df_compare['Eliminated'], df_formal['select']))'''

# # 產出及時結果
from tkinter import Text, Scrollbar, Button, messagebox

class TickerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("碳排預測結果")
        self.root.geometry("800x600")

        self.output_text = Text(root, wrap='word', height=20, width=70)
        self.output_text.pack(pady=20)

        self.save_button = Button(root, text="另存為CSV文件", command=self.save_to_csv)
        self.save_button.pack(pady=10)

    def save_to_csv(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if file_path:
            df_formal.to_csv(file_path, index=False)
            self.output_text.insert(tk.END, f"\n\n報告已保存為CSV文件：{file_path}")
            self.show_save_complete_message()

    def show_save_complete_message(self):
        messagebox.showinfo("儲存完畢", "報告已成功保存！")

def output_to_text_widget(df, col, co2, text_widget):
    Q_eliminate = df[col].sum()
    sum_co2_to_eliminate = df.loc[df[col] == 1, co2].sum()
    average_co2_to_eliminate = df.loc[df[col] == 1, co2].mean()
    year_co2_to_eliminate = sum_co2_to_eliminate * 41.1 * 1.6 * 365 / 1000000

    result_text = ('-------------預測結果-------------'
                    f"\n欲淘汰數量： {int(Q_eliminate)} 輛"
                    f"\n節省 CO2 Emissions 加總：{int(sum_co2_to_eliminate)} g/km"
                    f"\n節省 CO2 Emissions 平均：{round(average_co2_to_eliminate, 2)} g/km"
                    f"\n節省 CO2 Emissions 每年{round(year_co2_to_eliminate, 2)} 公噸"
                    f"\n>>大約等於 {round(year_co2_to_eliminate/15, 2)} 公頃森林的吸碳能力\n"
                    '\n\n-----各車種淘汰數量-----\n')

    # 列印每一車種的淘汰數量
    for key, total in selected_totals.items():
        result_text += f"{key} 的淘汰數量: {total}\n"


    text_widget.insert(tk.END, result_text)
    return sum_co2_to_eliminate

if __name__ == "__main__":
    root = tk.Tk()
    app = TickerApp(root)

    global forcast
    forcast = output_to_text_widget(df_formal, 'select', 'Predicted_CO2', app.output_text)

    root.mainloop()


actual = df_compare.loc[df_compare["Eliminated"] == 1, 'CO2 Emissions(g/km)'].sum()
print(f'\n\n每年 CO2 Emissions 節省量，實際與預測之誤差： { round((1 - forcast/actual)*100, 2)}%') 




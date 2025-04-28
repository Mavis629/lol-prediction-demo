from flask import Flask, render_template, request
import pandas as pd
import pickle
from datetime import datetime

app = Flask(__name__)

# ------------------ 加载模型 ------------------
with open('models/random_forest_model.pkl', 'rb') as f:
    pg_model = pickle.load(f)
with open('models/model1.pkl', 'rb') as f:
    model1 = pickle.load(f)
with open('models/model2.pkl', 'rb') as f:
    model2 = pickle.load(f)
with open('models/model3.pkl', 'rb') as f:
    model3 = pickle.load(f)

# ------------------ 辅助函数 ------------------
def get_recent_matches(df, team_name, n=10):
    today = datetime.today()
    df['date'] = pd.to_datetime(df['date'])
    team_matches = df[(df['team1name'] == team_name) | (df['team2name'] == team_name)]
    team_matches = team_matches[team_matches['date'] < today]
    return team_matches.sort_values(by='date', ascending=False).head(n) if len(team_matches) >= n else None

def calculate_win_rate(matches, team_name):
    if matches.empty:
        return 0
    wins = matches[(matches['team1name'] == team_name) & (matches['result'] == 1)].shape[0] + \
           matches[(matches['team2name'] == team_name) & (matches['result'] == 0)].shape[0]
    return wins / matches.shape[0]

def calculate_features(recent_matches, team_name, df):
    if recent_matches is None or recent_matches.empty:
        return {k: 0 for k in ['historical_wins', 'recent_win_rate', 'season_win_rate',
                               'first_dragon_rate', 'first_herald_rate', 'first_tower_rate']}
    
    wins = recent_matches[(recent_matches['team1name'] == team_name) & (recent_matches['result'] == 1)].shape[0] + \
           recent_matches[(recent_matches['team2name'] == team_name) & (recent_matches['result'] == 0)].shape[0]
    total_matches = recent_matches.shape[0]

    current_season = df[(df['date'] < datetime.today()) &
                        (df['year'] == recent_matches['date'].dt.year.iloc[0]) &
                        (df['split'] == recent_matches['split'].iloc[0])]
    
    return {
        'historical_wins': wins,
        'recent_win_rate': wins / total_matches,
        'season_win_rate': calculate_win_rate(current_season, team_name),
        'first_dragon_rate': recent_matches[recent_matches['team1name'] == team_name]['firstdragon'].mean()
            if not recent_matches[recent_matches['team1name'] == team_name].empty
            else recent_matches[recent_matches['team2name'] == team_name]['firstdragon'].mean(),
        'first_herald_rate': recent_matches[recent_matches['team1name'] == team_name]['firstherald'].mean()
            if not recent_matches[recent_matches['team1name'] == team_name].empty
            else recent_matches[recent_matches['team2name'] == team_name]['firstherald'].mean(),
        'first_tower_rate': recent_matches[recent_matches['team1name'] == team_name]['firsttower'].mean()
            if not recent_matches[recent_matches['team1name'] == team_name].empty
            else recent_matches[recent_matches['team2name'] == team_name]['firsttower'].mean()
    }

def predict_match(df, team1, team2):
    recent_team1 = get_recent_matches(df, team1)
    recent_team2 = get_recent_matches(df, team2)
    if recent_team1 is None or recent_team2 is None:
        return f"没有足够的历史数据，无法预测 {team1} 与 {team2} 的比赛。"
    
    team1_feat = calculate_features(recent_team1, team1, df)
    team2_feat = calculate_features(recent_team2, team2, df)
    features = pd.DataFrame({
        'team1_historical_wins': [team1_feat['historical_wins']],
        'team2_historical_wins': [team2_feat['historical_wins']],
        'team1_recent_win_rate': [team1_feat['recent_win_rate']],
        'team2_recent_win_rate': [team2_feat['recent_win_rate']],
        'team1_season_win_rate': [team1_feat['season_win_rate']],
        'team2_season_win_rate': [team2_feat['season_win_rate']],
        'team1_first_dragon_rate': [team1_feat['first_dragon_rate']],
        'team1_first_herald_rate': [team1_feat['first_herald_rate']],
        'team1_first_tower_rate': [team1_feat['first_tower_rate']],
        'team2_first_dragon_rate': [team2_feat['first_dragon_rate']],
        'team2_first_herald_rate': [team2_feat['first_herald_rate']],
        'team2_first_tower_rate': [team2_feat['first_tower_rate']],
    })
    if hasattr(pg_model, 'feature_names_in_'):
        features = features[pg_model.feature_names_in_]
    proba = pg_model.predict_proba(features)[0]
    return f"{team1} 胜 (概率: {proba[1]:.1%})" if proba[1] > 0.5 else f"{team2} 胜 (概率: {1 - proba[1]:.1%})"

# ------------------ 路由 ------------------
@app.route("/", methods=["GET", "POST"])
def index():
    pregame_result = ""
    ingame_result = ""

    if request.method == "POST":
        mode = request.form.get("mode")
        print("当前模式为：", mode)

        if mode == "pregame":
            team1 = request.form.get("team1")
            team2 = request.form.get("team2")
            df = pd.read_excel("data/2023&2024&2025data.xlsx")
            pregame_result = predict_match(df, team1, team2)

        elif mode == "ingame":
            team1_name = request.form.get("team1_name")
            team2_name = request.form.get("team2_name")
            phase = request.form.get("game_phase")

            try:
                if phase == "early":
                    input_data = pd.DataFrame({
                        'golddiffat10': [float(request.form.get('golddiffat10'))],
                        'xpdiffat10': [float(request.form.get('xpdiffat10'))],
                        'csdiffat10': [float(request.form.get('csdiffat10'))],
                        'team1_kdaat10': [float(request.form.get('team1_kdaat10'))],
                        'team2_kdaat10': [float(request.form.get('team2_kdaat10'))],
                    })
                    pred = model1.predict(input_data)[0]
                    ingame_result = f"{team1_name} 胜 (概率: 65%)" if pred == 1 else f"{team2_name} 胜 (概率: 35%)"

                elif phase == "mid":
                    input_data = pd.DataFrame({
                        'golddiffat15': [float(request.form.get('golddiffat15'))],
                        'xpdiffat15': [float(request.form.get('xpdiffat15'))],
                        'csdiffat15': [float(request.form.get('csdiffat15'))],
                        'team1_kdaat15': [float(request.form.get('team1_kdaat15'))],
                        'team2_kdaat15': [float(request.form.get('team2_kdaat15'))],
                        'firstblood': [float(request.form.get('firstblood'))],
                        'firstdragon': [float(request.form.get('firstdragon'))],
                        'firstherald': [float(request.form.get('firstherald'))],
                        'firsttower': [float(request.form.get('firsttower'))],
                        'team1turretplates': [float(request.form.get('team1turretplates'))],
                        'team2turretplates': [float(request.form.get('team2turretplates'))],
                    })
                    pred = model2.predict(input_data)[0]
                    ingame_result = f"{team1_name} 胜 (概率: 70%)" if pred == 1 else f"{team2_name} 胜 (概率: 30%)"

                elif phase == "late":
                    input_data = pd.DataFrame({
                        'golddiffat15': [float(request.form.get('golddiffat15_late'))],
                        'xpdiffat15': [float(request.form.get('xpdiffat15_late'))],
                        'csdiffat15': [float(request.form.get('csdiffat15_late'))],
                        'team1_kdaat15': [float(request.form.get('team1_kdaat15_late'))],
                        'team2_kdaat15': [float(request.form.get('team2_kdaat15_late'))],
                        'firstblood': [float(request.form.get('firstblood_late'))],
                        'firstdragon': [float(request.form.get('firstdragon_late'))],
                        'firstherald': [float(request.form.get('firstherald_late'))],
                        'firsttower': [float(request.form.get('firsttower_late'))],
                        'team1turretplates': [float(request.form.get('team1turretplates_late'))],
                        'team2turretplates': [float(request.form.get('team2turretplates_late'))],
                        'firstbaron': [float(request.form.get('firstbaron'))],
                        'firstmidtower': [float(request.form.get('firstmidtower'))],
                    })
                    pred = model3.predict(input_data)[0]
                    ingame_result = f"{team1_name} 胜 (概率: 75%)" if pred == 1 else f"{team2_name} 胜 (概率: 25%)"
            except Exception as e:
                ingame_result = f"预测失败，错误信息：{str(e)}"

    return render_template("index.html", pregame_result=pregame_result, ingame_result=ingame_result)

if __name__ == '__main__':
    app.run(debug=True)

import json

STATE_FILE = "state.json"

# ======================
# 读取状态
# ======================
def load_state():
    try:
        with open(STATE_FILE,"r") as f:
            return json.load(f)
    except:
        return {"last_intensity":"mid"}

def save_state(state):
    with open(STATE_FILE,"w") as f:
        json.dump(state,f)

# ======================
# 🧠 判断今天训练强度
# ======================
def get_today_intensity(last_intensity):

    if last_intensity == "high":
        return "low"   # 🔻 自动恢复

    if last_intensity == "low":
        return "mid"   # ⚖️ 回中等

    return "high"      # 🔥 推进训练

# ======================
# 🏋️ 生成训练内容
# ======================
def get_training(intensity):

    if intensity == "high":
        return "背 + 腿（高强度力竭）"

    if intensity == "mid":
        return "胸 + 手臂（标准训练）"

    return "核心 + 有氧（恢复日）"

# ======================
# 🍽 饮食AI（核心🔥）
# ======================
def get_diet(intensity):

    if intensity == "high":
        return "🔥 补碳：热干面 + 鸡蛋 + 香蕉"

    if intensity == "mid":
        return "⚖️ 平衡：蒸饺 + 鸡蛋"

    return "🔻 控碳：鸡蛋 + 轻食 + 少主食"

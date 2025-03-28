import streamlit as st
import pycuber as pc
import kociemba
import matplotlib.pyplot as plt
import random
from io import BytesIO
from collections import Counter
import re

# ---------- 顏色對應 ----------
color_map = {
    'white': 'white',
    'yellow': 'yellow',
    'red': 'red',
    'orange': 'orange',
    'blue': 'blue',
    'green': 'green'
}

face_names = {
    'U': '上(U)',
    'R': '右(R)',
    'F': '前(F)',
    'D': '下(D)',
    'L': '左(L)',
    'B': '後(B)'
}

# ---------- WCA 標準 Facelet 顏色對應 ----------
facelet_to_color = {
    'U': 'yellow',
    'R': 'red',
    'F': 'green',
    'D': 'white',
    'L': 'orange',
    'B': 'blue'
}

# ---------- 畫單一面 ----------
def draw_face(ax, face, start_x, start_y, colour_to_facelet, facelet_index_start, face_name):
    face_flip = {
        'U': (True, False),
        'D': (True, False),
        'F': (True, False),
        'B': (True, False),
        'L': (True, False),
        'R': (True, False)
    }
    flip_vert, flip_horiz = face_flip.get(face_name, (False, False))
    
    for i in range(3):
        for j in range(3):
            ii = 2 - i if flip_vert else i
            jj = 2 - j if flip_horiz else j
            sticker_colour = face[ii][jj].colour  # e.g., 'red'
            facelet = colour_to_facelet[sticker_colour]  # e.g., 'R'
            color = facelet_to_color[facelet]  # e.g., 'red'
            square = plt.Rectangle((start_x + j, start_y + i), 1, 1,
                                   facecolor=color, edgecolor='black')
            ax.add_patch(square)
            
            # 添加數字標記（全局索引 +1 以符合人類計數習慣）
            global_index = facelet_index_start + ii*3 + jj + 1
            ax.text(start_x + j + 0.5, start_y + i + 0.5, 
                    str(global_index),
                    ha='center', va='center', 
                    fontsize=8, color='black')

# ---------- 畫整個方塊 ----------
def draw_cube(cube):
    fig, ax = plt.subplots()
    ax.set_aspect('equal')
    ax.axis('off')

    # 依中心塊顏色建立 color → facelet 對應
    colour_to_facelet = {
        cube.get_face('U')[1][1].colour: 'U',
        cube.get_face('R')[1][1].colour: 'R',
        cube.get_face('F')[1][1].colour: 'F',
        cube.get_face('D')[1][1].colour: 'D',
        cube.get_face('L')[1][1].colour: 'L',
        cube.get_face('B')[1][1].colour: 'B'
    }

    # 畫面位置配置 (x, y, facelet_index_start)
    face_coords = {
        'U': (3, 9, 0),    # 上面從0開始
        'L': (0, 6, 36),   # 左面從36開始
        'F': (3, 6, 18),   # 前面從18開始
        'R': (6, 6, 9),    # 右面從9開始
        'B': (9, 6, 45),   # 後面從45開始
        'D': (3, 3, 27)    # 下面從27開始
    }

    for face in ['U', 'L', 'F', 'R', 'B', 'D']:
        face_data = cube.get_face(face)
        x, y, index_start = face_coords[face]  # 解包三个值
        draw_face(ax, face_data, x, y, colour_to_facelet, index_start, face)

    ax.set_xlim(0, 12)
    ax.set_ylim(0, 12)

    buf = BytesIO()
    plt.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    return buf

# ---------- 工具 ----------
def generate_scramble(n=20):
    moves = ['U', 'D', 'L', 'R', 'F', 'B']
    suffixes = ['', "'", '2']
    scramble = []
    prev_move = ''
    for _ in range(n):
        move = random.choice(moves)
        while move == prev_move:
            move = random.choice(moves)
        prev_move = move
        scramble.append(move + random.choice(suffixes))
    return ' '.join(scramble)

def to_facelet_str(cube):
    face_order = ['U', 'R', 'F', 'D', 'L', 'B']
    colour_to_facelet = {
        cube.get_face('U')[1][1].colour: 'U',
        cube.get_face('R')[1][1].colour: 'R',
        cube.get_face('F')[1][1].colour: 'F',
        cube.get_face('D')[1][1].colour: 'D',
        cube.get_face('L')[1][1].colour: 'L',
        cube.get_face('B')[1][1].colour: 'B'
    }
    result = ''
    for face in face_order:
        for row in cube.get_face(face):
            for sticker in row:
                result += colour_to_facelet[sticker.colour]
    return result

# ---------- Streamlit App ----------
st.set_page_config(page_title="魔術方塊還原動畫", layout="centered")
st.title("🧊 魔術方塊還原動畫器")

if "states" not in st.session_state:
    solved_cube = pc.Cube()
    st.session_state.states = [solved_cube]
    st.session_state.current_step = 0
    st.session_state.scramble = "（初始化）"
    st.session_state.solution = ""

# ---------- 打亂按鈕 ----------
if st.button("🎲 隨機打亂方塊"):
    scramble = generate_scramble()
    cube = pc.Cube()
    cube(pc.Formula(scramble))
    facelets = to_facelet_str(cube)
    try:
        solution = kociemba.solve(facelets)
        st.session_state.scramble = scramble
        st.session_state.solution = solution
        st.session_state.states = [cube.copy()]
        for move in solution.split():
            cube(move)
            st.session_state.states.append(cube.copy())
        st.session_state.current_step = 0
    except Exception as e:
        st.error(f"❌ 打亂錯誤：{e}")

# ---------- 使用者輸入打亂公式 ----------
st.subheader("🌀 輸入打亂公式")
formula_input = st.text_input("請輸入打亂公式（如：R U R' U'）：")

if st.button("✅ 套用打亂公式"):
    try:
        moves = re.findall(r"[URFDLB][2']?", formula_input.upper())
        scramble = ' '.join(moves)
        cube = pc.Cube()
        cube(pc.Formula(scramble))
        facelets = to_facelet_str(cube)
        solution = kociemba.solve(facelets)
        st.session_state.scramble = scramble
        st.session_state.solution = solution
        st.session_state.states = [cube.copy()]
        for move in solution.split():
            cube(move)
            st.session_state.states.append(cube.copy())
        st.session_state.current_step = 0
    except Exception as e:
        st.error(f"❌ 打亂公式錯誤：{e}")



# ---------- 顏色代碼轉合法 Facelet 檢查 ----------
st.subheader("🌈 顏色代碼轉 Facelet 字串並驗證")

color_code_input = st.text_area("請輸入 54 個顏色代碼字元（例如：o, r, w, b, y, g）")

color_mapping = {
    'o': 'L',  # orange
    'r': 'R',  # red
    'w': 'U',  # white
    'b': 'B',  # blue
    'y': 'D',  # yellow
    'g': 'F'   # green
}

if st.button("🎨 轉換並驗證 Facelet 字串"):
    cleaned = color_code_input.strip().lower().replace(' ', '')
    if len(cleaned) != 54:
        st.error("❌ 請輸入剛好 54 個字元的顏色代碼。")
    elif any(c not in color_mapping for c in cleaned):
        st.error(f"❌ 發現未定義的顏色字元：{set(c for c in cleaned if c not in color_mapping)}")
    else:
        try:
            converted = ''.join(color_mapping[c] for c in cleaned)
            st.session_state.converted_facelet = converted
            st.success("✅ 轉換成功！")
            st.text_area("🔁 轉換後的 Facelet 字串：", value=converted, height=100)

            # 嘗試還原，驗證是否合法
            try:
                _ = kociemba.solve(converted)
                st.success("✅ 這是一個合法的魔術方塊狀態！可以還原的。")
            except Exception as e:
                st.error(f"❌ 無法還原，這是一個非法的狀態。\n錯誤訊息：{e}")

        except Exception as e:
            st.error(f"❌ 發生轉換錯誤：{e}")


# ---------- 使用者輸入 Facelet 字串 ----------
st.subheader("🎨 輸入 Facelet 字串（共 54 字元）")
if 'converted_facelet' not in st.session_state:
    st.session_state.converted_facelet = ''

# 创建可交互的text_area，并与session state关联
facelet_input = st.text_area(
    "請輸入 54 個 URFDLB 字元：",
    value=st.session_state.converted_facelet,
    key="converted_facelet"  # 这是关键：添加key来关联session state
)

input_str = facelet_input.strip().upper()
input_len = len(input_str)
invalid_chars = [c for c in input_str if c not in "URFDLB"]

# 顯示長度與非法字元提示
st.markdown(f"🔢 你輸入了 **{input_len}** 個字元。")
if invalid_chars:
    st.warning(f"⚠️ 發現非法字元：{set(invalid_chars)}")

# ---------- Facelet 預覽（不解） ----------
if st.button("📸 預覽輸入狀態（不解）"):
    if input_len != 54:
        st.error("❌ 字元數量錯誤，請輸入剛好 54 個 URFDLB 字元。")
    elif invalid_chars:
        st.error("❌ 含有非法字元，僅能包含 U、R、F、D、L、B。")
    else:
        try:
            solution = kociemba.solve(input_str)
            cube = pc.Cube()
            for move in solution.split()[::-1]:
                if move.endswith("'"):
                    cube(move[:-1])
                elif move.endswith("2"):
                    cube(move)
                else:
                    cube(move + "'")
            st.session_state.states = [cube.copy()]
            st.session_state.scramble = "（Facelet 預覽）"
            st.session_state.solution = ""
            st.session_state.current_step = 0
        except Exception as e:
            st.error(f"❌ 預覽錯誤：{e}")



# ---------- 執行還原解法 ----------
if st.button("🧠 開始解法還原"):
    input_str = st.session_state.converted_facelet
    input_len = len(input_str)
    if input_len != 54:
        st.error("❌ 字元數量錯誤，請輸入剛好 54 個 URFDLB 字元。")
    elif invalid_chars:
        st.error("❌ 含有非法字元，僅能包含 U、R、F、D、L、B。")
    else:
        facelet_count = Counter(input_str)
        with st.expander("📈 Facelet 字元分布分析"):
            for face in "URFDLB":
                count = facelet_count.get(face, 0)
                st.markdown(f"{face_names[face]}：{'🟥' if count > 9 else '🟩' if count == 9 else '🟨'} {count} 個")

        if any(v != 9 for v in facelet_count.values()):
            st.error(f"❌ Facelet 字元數量錯誤：{dict(facelet_count)}")
        else:
            try:
                solution = kociemba.solve(input_str)
                
                # 從還原狀態開始反推回 scramble 狀態
                cube = pc.Cube()
                reversed_moves = []
                for move in solution.split()[::-1]:  # 反轉順序
                    if move.endswith("'"):
                        reversed_moves.append(move[:-1])  # R' → R
                    elif move.endswith("2"):
                        reversed_moves.append(move)      # R2 → R2
                    else:
                        reversed_moves.append(move + "'")  # R → R'

                for move in reversed_moves:
                    cube(move)

                # 加入原始狀態後再執行正向解法動畫
                st.session_state.states = [cube.copy()]
                for move in solution.split():
                    cube(move)
                    st.session_state.states.append(cube.copy())

                st.session_state.scramble = "（由 Facelet 解法）"
                st.session_state.solution = solution
                st.session_state.current_step = 0
            except Exception as e:
                st.error(f"❌ 解法錯誤：{e}")

# ---------- 顯示動畫 ----------
if st.session_state.states:
    st.info(f"打亂步驟：{st.session_state.scramble}")
    st.info(f"解法步驟（共 {len(st.session_state.states) - 1} 步）：{st.session_state.solution}")

    # 顯示目前步驟的 cube 狀態圖片
    current_cube = st.session_state.states[st.session_state.current_step]
    buf = draw_cube(current_cube)
    st.image(buf, caption=f"第 {st.session_state.current_step} 步")

    # 添加预设公式选择
    preset_formulas = {
        "(右手上左下右)R U R' U'": "R U R' U'",
        "(左手上右下左)L' U' L U": "L' U' L U",
        "(右手上左下右90)B U B' U'":"B U B' U'",
        "(左手上右下左90)F' U' F U":"F' U' F U",
        "(右手上左下右180)L U L' U'": "L U L' U'",
        "(左手上右下左180)R' U' R U": "R' U' R U",
        
        "(右手上左下右270)F U F' U'":"F U F' U'",
        "(左手上右下左270)B' U' B U":"B' U' B U",
        
        
        "(右手小魚)R U R' U R U' U' R'":"R U R' U R U' U' R'",
        "(左手小魚)L' U' L U' L' U U L":"L' U' L U' L' U U L",
        "(雙蚯蚓)R U' L' U R' U' L":"R U' L' U R' U' L",
        "(右手小魚 90)B U B' U B U' U' B'":"B U B' U B U' U' B'",
        "(右手小魚 180)L U L' U L U' U' L'":"L U L' U L U' U' L'",
        "(右手小魚 270)F U F' U F U' U' F'":"F U F' U F U' U' F'",
        "(左手小魚 90)F' U' F U' F' U U F":"F' U' F U' F' U U F",
        "(左手小魚 180)R' U' R U' R' U U R":"R' U' R U' R' U U R",
        "(左手小魚 270)B' U' B U' B' U U B":"B' U' B U' B' U U B",
        
        
    }
    
    selected_formula = st.selectbox(
        "🔄 选择预设旋转公式(上左下右)：",
        options=list(preset_formulas.keys()),
        index=0
    )
    
    # 添加自定义公式输入
    custom_formula = st.text_input(
        "🔄 或输入自定义旋转公式（如：R U R' U'）：",
        value=preset_formulas[selected_formula]
    )
    
    # 使用选择的公式或自定义公式
    rotate_formula = custom_formula

    # 添加六面旋轉按鈕
    st.write("快速旋轉按鈕：")
    
    # 第一行：U面和D面
    col_u1, col_u2, col_d1, col_d2 = st.columns(4)
    with col_u1:
        if st.button("U ↻"):
            rotate_formula = "U"
            moves = [rotate_formula]
            new_cube = current_cube.copy()
            new_cube(pc.Formula(' '.join(moves)))
            st.session_state.states = st.session_state.states[:st.session_state.current_step + 1]
            st.session_state.states.append(new_cube)
            st.session_state.current_step += 1
            st.rerun()
    with col_u2:
        if st.button("U' ↺"):
            rotate_formula = "U'"
            moves = [rotate_formula]
            new_cube = current_cube.copy()
            new_cube(pc.Formula(' '.join(moves)))
            st.session_state.states = st.session_state.states[:st.session_state.current_step + 1]
            st.session_state.states.append(new_cube)
            st.session_state.current_step += 1
            st.rerun()
    with col_d1:
        if st.button("D ↻"):
            rotate_formula = "D"
            moves = [rotate_formula]
            new_cube = current_cube.copy()
            new_cube(pc.Formula(' '.join(moves)))
            st.session_state.states = st.session_state.states[:st.session_state.current_step + 1]
            st.session_state.states.append(new_cube)
            st.session_state.current_step += 1
            st.rerun()
    with col_d2:
        if st.button("D' ↺"):
            rotate_formula = "D'"
            moves = [rotate_formula]
            new_cube = current_cube.copy()
            new_cube(pc.Formula(' '.join(moves)))
            st.session_state.states = st.session_state.states[:st.session_state.current_step + 1]
            st.session_state.states.append(new_cube)
            st.session_state.current_step += 1
            st.rerun()

    # 第二行：R面和L面
    col_r1, col_r2, col_l1, col_l2 = st.columns(4)
    with col_r1:
        if st.button("R ↻"):
            rotate_formula = "R"
            moves = [rotate_formula]
            new_cube = current_cube.copy()
            new_cube(pc.Formula(' '.join(moves)))
            st.session_state.states = st.session_state.states[:st.session_state.current_step + 1]
            st.session_state.states.append(new_cube)
            st.session_state.current_step += 1
            st.rerun()
    with col_r2:
        if st.button("R' ↺"):
            rotate_formula = "R'"
            moves = [rotate_formula]
            new_cube = current_cube.copy()
            new_cube(pc.Formula(' '.join(moves)))
            st.session_state.states = st.session_state.states[:st.session_state.current_step + 1]
            st.session_state.states.append(new_cube)
            st.session_state.current_step += 1
            st.rerun()
    with col_l1:
        if st.button("L ↻"):
            rotate_formula = "L"
            moves = [rotate_formula]
            new_cube = current_cube.copy()
            new_cube(pc.Formula(' '.join(moves)))
            st.session_state.states = st.session_state.states[:st.session_state.current_step + 1]
            st.session_state.states.append(new_cube)
            st.session_state.current_step += 1
            st.rerun()
    with col_l2:
        if st.button("L' ↺"):
            rotate_formula = "L'"
            moves = [rotate_formula]
            new_cube = current_cube.copy()
            new_cube(pc.Formula(' '.join(moves)))
            st.session_state.states = st.session_state.states[:st.session_state.current_step + 1]
            st.session_state.states.append(new_cube)
            st.session_state.current_step += 1
            st.rerun()

    # 第三行：F面和B面
    col_f1, col_f2, col_b1, col_b2 = st.columns(4)
    with col_f1:
        if st.button("F ↻"):
            rotate_formula = "F"
            moves = [rotate_formula]
            new_cube = current_cube.copy()
            new_cube(pc.Formula(' '.join(moves)))
            st.session_state.states = st.session_state.states[:st.session_state.current_step + 1]
            st.session_state.states.append(new_cube)
            st.session_state.current_step += 1
            st.rerun()
    with col_f2:
        if st.button("F' ↺"):
            rotate_formula = "F'"
            moves = [rotate_formula]
            new_cube = current_cube.copy()
            new_cube(pc.Formula(' '.join(moves)))
            st.session_state.states = st.session_state.states[:st.session_state.current_step + 1]
            st.session_state.states.append(new_cube)
            st.session_state.current_step += 1
            st.rerun()
    with col_b1:
        if st.button("B ↻"):
            rotate_formula = "B"
            moves = [rotate_formula]
            new_cube = current_cube.copy()
            new_cube(pc.Formula(' '.join(moves)))
            st.session_state.states = st.session_state.states[:st.session_state.current_step + 1]
            st.session_state.states.append(new_cube)
            st.session_state.current_step += 1
            st.rerun()
    with col_b2:
        if st.button("B' ↺"):
            rotate_formula = "B'"
            moves = [rotate_formula]
            new_cube = current_cube.copy()
            new_cube(pc.Formula(' '.join(moves)))
            st.session_state.states = st.session_state.states[:st.session_state.current_step + 1]
            st.session_state.states.append(new_cube)
            st.session_state.current_step += 1
            st.rerun()

    # 添加中心层旋转按钮
    st.write("M层（中间层）、E层（赤道层）、S层（站立层）中心层 旋转按钮：")
    
    # M层（中间层）、E层（赤道层）、S层（站立层）
    col_m1, col_m2, col_e1, col_e2, col_s1, col_s2 = st.columns(6)
    
    with col_m1:
        if st.button("M ↻"):
            rotate_formula = "L' R"
            moves = re.findall(r"[URFDLB][2']?", rotate_formula.upper())
            new_cube = current_cube.copy()
            new_cube(pc.Formula(' '.join(moves)))
            st.session_state.states = st.session_state.states[:st.session_state.current_step + 1]
            st.session_state.states.append(new_cube)
            st.session_state.current_step += 1
            st.rerun()
            
    with col_m2:
        if st.button("M' ↺"):
            rotate_formula = "L R'"
            moves = re.findall(r"[URFDLB][2']?", rotate_formula.upper())
            new_cube = current_cube.copy()
            new_cube(pc.Formula(' '.join(moves)))
            st.session_state.states = st.session_state.states[:st.session_state.current_step + 1]
            st.session_state.states.append(new_cube)
            st.session_state.current_step += 1
            st.rerun()
            
    with col_e1:
        if st.button("E ↻"):
            rotate_formula = "U D'"
            moves = re.findall(r"[URFDLB][2']?", rotate_formula.upper())
            new_cube = current_cube.copy()
            new_cube(pc.Formula(' '.join(moves)))
            st.session_state.states = st.session_state.states[:st.session_state.current_step + 1]
            st.session_state.states.append(new_cube)
            st.session_state.current_step += 1
            st.rerun()
            
    with col_e2:
        if st.button("E' ↺"):
            rotate_formula = "U' D"
            moves = re.findall(r"[URFDLB][2']?", rotate_formula.upper())
            new_cube = current_cube.copy()
            new_cube(pc.Formula(' '.join(moves)))
            st.session_state.states = st.session_state.states[:st.session_state.current_step + 1]
            st.session_state.states.append(new_cube)
            st.session_state.current_step += 1
            st.rerun()
            
    with col_s1:
        if st.button("S ↻"):
            rotate_formula = "F' B"
            moves = re.findall(r"[URFDLB][2']?", rotate_formula.upper())
            new_cube = current_cube.copy()
            new_cube(pc.Formula(' '.join(moves)))
            st.session_state.states = st.session_state.states[:st.session_state.current_step + 1]
            st.session_state.states.append(new_cube)
            st.session_state.current_step += 1
            st.rerun()
            
    with col_s2:
        if st.button("S' ↺"):
            rotate_formula = "F B'"
            moves = re.findall(r"[URFDLB][2']?", rotate_formula.upper())
            new_cube = current_cube.copy()
            new_cube(pc.Formula(' '.join(moves)))
            st.session_state.states = st.session_state.states[:st.session_state.current_step + 1]
            st.session_state.states.append(new_cube)
            st.session_state.current_step += 1
            st.rerun()

    # 執行旋轉公式按鈕
    if st.button("↻ 執行旋轉公式"):
        try:
            moves = re.findall(r"[URFDLB][2']?", rotate_formula.upper())
            if moves:
                new_cube = current_cube.copy()
                new_cube(pc.Formula(' '.join(moves)))
                st.session_state.states = st.session_state.states[:st.session_state.current_step + 1]
                st.session_state.states.append(new_cube)
                st.session_state.current_step += 1
                st.rerun()
        except Exception as e:
            st.error(f"❌ 旋轉公式錯誤：{e}")

    # 控制步驟按鈕
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("⏮️ 上一步") and st.session_state.current_step > 0:
            st.session_state.current_step -= 1
            st.rerun()  # ✅ 使用新版 API

    with col2:
        st.write(f"第 {st.session_state.current_step} / {len(st.session_state.states) - 1} 步")

    with col3:
        if st.button("⏭️ 下一步") and st.session_state.current_step < len(st.session_state.states) - 1:
            st.session_state.current_step += 1
            st.rerun()  # ✅ 使用新版 API

    # 顯示目前 Facelet 字串
    def cube_to_facelet_str(cube):
        face_order = ['U', 'R', 'F', 'D', 'L', 'B']
        colour_to_facelet = {
            cube.get_face('U')[1][1].colour: 'U',
            cube.get_face('R')[1][1].colour: 'R',
            cube.get_face('F')[1][1].colour: 'F',
            cube.get_face('D')[1][1].colour: 'D',
            cube.get_face('L')[1][1].colour: 'L',
            cube.get_face('B')[1][1].colour: 'B'
        }
        result = ''
        for face in face_order:
            for row in cube.get_face(face):
                for sticker in row:
                    result += colour_to_facelet[sticker.colour]
        return result

    facelet_now = cube_to_facelet_str(current_cube)
    st.text_area("🧾 目前狀態 Facelet 字串（可複製）：", value=facelet_now, height=100, key="facelet_now_display")

    # ---------- 顯示目前狀態的 Facelet 字串 ----------
    def cube_to_facelet_str(cube):
        face_order = ['U', 'R', 'F', 'D', 'L', 'B']
        colour_to_facelet = {
            cube.get_face('U')[1][1].colour: 'U',
            cube.get_face('R')[1][1].colour: 'R',
            cube.get_face('F')[1][1].colour: 'F',
            cube.get_face('D')[1][1].colour: 'D',
            cube.get_face('L')[1][1].colour: 'L',
            cube.get_face('B')[1][1].colour: 'B'
        }
        result = ''
        for face in face_order:
            for row in cube.get_face(face):
                for sticker in row:
                    result += colour_to_facelet[sticker.colour]
        return result

    facelet_now = cube_to_facelet_str(st.session_state.states[st.session_state.current_step])
    #st.text_area("🧾 目前狀態 Facelet 字串（可複製）：", value=facelet_now, height=100)

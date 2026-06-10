#!/usr/bin/env python3
"""Generate 10 C++ DSA course PDFs from 2026fare source materials."""

from __future__ import annotations

import textwrap
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
)

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "root_data" / "课程资料"
FONT_PATH = "C:/Windows/Fonts/msyh.ttc"
FONT_NAME = "MSYaHei"
CODE_FONT = "Courier"


def register_fonts() -> None:
    pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_PATH, subfontIndex=0))


def build_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "title",
            fontName=FONT_NAME,
            fontSize=22,
            leading=28,
            spaceAfter=12,
            textColor=colors.HexColor("#1a365d"),
        ),
        "subtitle": ParagraphStyle(
            "subtitle",
            fontName=FONT_NAME,
            fontSize=14,
            leading=20,
            spaceAfter=8,
            textColor=colors.HexColor("#2c5282"),
        ),
        "heading": ParagraphStyle(
            "heading",
            fontName=FONT_NAME,
            fontSize=13,
            leading=18,
            spaceBefore=10,
            spaceAfter=6,
            textColor=colors.HexColor("#2d3748"),
        ),
        "body": ParagraphStyle(
            "body",
            fontName=FONT_NAME,
            fontSize=10.5,
            leading=16,
            spaceAfter=6,
            alignment=TA_LEFT,
        ),
        "bullet": ParagraphStyle(
            "bullet",
            fontName=FONT_NAME,
            fontSize=10.5,
            leading=16,
            leftIndent=14,
            spaceAfter=4,
        ),
        "code_title": ParagraphStyle(
            "code_title",
            fontName=FONT_NAME,
            fontSize=10,
            leading=14,
            spaceBefore=6,
            spaceAfter=2,
            textColor=colors.HexColor("#4a5568"),
        ),
    }


def code_block(text: str, styles: dict) -> list:
    wrapped = text.rstrip("\n")
    return [
        Preformatted(
            wrapped,
            ParagraphStyle(
                "pre",
                fontName=CODE_FONT,
                fontSize=8,
                leading=10,
                backColor=colors.HexColor("#f7fafc"),
                borderColor=colors.HexColor("#e2e8f0"),
                borderWidth=0.5,
                borderPadding=6,
            ),
        ),
        Spacer(1, 0.15 * cm),
    ]


def esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def section(title: str, styles: dict) -> Paragraph:
    return Paragraph(esc(title), styles["heading"])


def bullets(items: list[str], styles: dict) -> list:
    return [Paragraph(f"• {esc(item)}", styles["bullet"]) for item in items]


# ---------------------------------------------------------------------------
# Course content definitions
# ---------------------------------------------------------------------------

COURSES: list[dict] = [
    {
        "filename": "01_C++竞赛基础与STL容器.pdf",
        "title": "第01课：C++ 竞赛基础与 STL 容器",
        "subtitle": "面向算法竞赛的 C++ 编程基础 · 标准模板库核心容器",
        "source_files": [
            "C++标准库.cpp", "STL01.cpp", "map-P1102对数.cpp",
            "set-lower-prev-P2234营业额统计.cpp", "deque-P10457占卜DIY.cpp",
            "hash-哈希表.cpp", "operator-结构体.cpp", "nth_element-P1923求第k小的数.cpp",
        ],
        "objectives": [
            "掌握竞赛常用头文件、类型别名与 I/O 加速写法",
            "熟练使用 vector、map、set、deque、unordered_map 等 STL 容器",
            "理解 pair、bitset 及自定义结构体排序/比较",
            "了解 nth_element 部分排序的用法与复杂度",
        ],
        "concepts": [
            ("竞赛模板", "常用 `#include <bits/stdc++.h>` 一次性引入标准库；`ios::sync_with_stdio(false)` 与 `cin.tie(0)` 关闭同步加速输入；`typedef long long ll` 防止溢出。"),
            ("vector", "动态数组，支持下标访问、push_back、resize；适合存储序列数据，是算法题最常用的容器。"),
            ("map / set", "map 为键值对有序容器（红黑树），set 为有序集合；查找/插入/删除均为 O(log n)。`lower_bound`、`upper_bound` 用于找前驱后继。"),
            ("unordered_map", "哈希表实现，平均 O(1) 查找；键需可哈希，无序存储，适合计数与快速查询。"),
            ("deque", "双端队列，头尾 O(1) 插入删除，支持下标访问，适合滑动窗口与 BFS。"),
            ("bitset", "定长位集，空间约为 bool 数组的 1/8；支持 set/reset/flip、位运算，常用于素数筛与状态压缩。"),
            ("nth_element", "将第 k 小元素放到正确位置，左侧不大于、右侧不小于，平均 O(n)，比完整 sort 更快。"),
        ],
        "tips": [
            "map/set 的 key 必须支持 `<` 比较；unordered_map 的 key 需支持 hash 与 `==`。",
            "自定义结构体放入 set/map 需重载 `<` 或提供比较函数/lambda。",
            "vector 下标从 0 开始，竞赛题常从下标 1 开始存数据，注意边界。",
            "long long 范围约 ±9e18，乘法前判断是否溢出。",
        ],
        "examples": [
            (
                "STL 容器速查（map / set / pair）",
                """// map: 键值对有序容器
map<string, int> mp;
mp["apple"] = 3;
mp.insert({"banana", 5});
if (mp.count("apple")) cout << mp["apple"];

// set: 有序集合，元素唯一
set<int> st = {3, 1, 4};
st.insert(2);
auto it = st.lower_bound(3);  // >=3 的第一个元素

// pair: 二元组，常用于排序
vector<pair<int,int>> v;
sort(v.begin(), v.end());  // 先比 first 再比 second""",
            ),
            (
                "bitset 基本操作（摘自 C++标准库.cpp）",
                """bitset<1000005> bs;       // 约 125KB，100 万位
bs.set(5);                  // 第 5 位置 1
bs.reset(5);                // 第 5 位置 0
bs.flip(5);                 // 翻转第 5 位
bool b = bs[5];             // 读取某位
int cnt = bs.count();       // 统计 1 的个数
string s = bs.to_string(); // 转二进制字符串

// 空间对比：1000 万 bool 约 10MB，bitset 约 1.25MB""",
            ),
            (
                "nth_element 部分排序",
                """vector<ll> t = a;
// 将前 k 大的元素放到 [1,k] 区间（降序）
nth_element(t.begin()+1, t.begin()+1+k, t.end(), greater<ll>());
// 时间复杂度 O(n)，比 sort 的 O(n log n) 更快""",
            ),
        ],
        "problems": ["P1102 对数", "P2234 营业额统计", "P1923 求第 k 小的数", "P10457 占卜 DIY"],
    },
    {
        "filename": "02_字符串处理.pdf",
        "title": "第02课：字符串处理",
        "subtitle": "C++ string 类 · 子串匹配 · 字典序 · 字符串哈希",
        "source_files": [
            "字符串01.cpp", "字符串02.cpp", "字符串03.cpp",
            "string-字符串转小写.cpp", "字符串-B2118验证子串.cpp",
            "字符串-字典序.cpp", "字符串哈希-模板-P3370.cpp",
            "字符串哈希-P10468兔子与兔子.cpp", "01字符串分割.cpp",
        ],
        "objectives": [
            "掌握 string 的构造、拼接、查找、插入、删除、替换、substr",
            "理解迭代器遍历与 reverse 反转",
            "学会子串验证、字典序比较与大小写转换",
            "掌握字符串哈希（滚动哈希）原理与去重应用",
        ],
        "concepts": [
            ("string 基础", "C++ string 支持 `+` 拼接、`push_back/pop_back`、`size/length`；`find` 返回 npos 表示未找到；`substr(pos, len)` 取子串。"),
            ("迭代器", "`string::iterator` 可正向/反向遍历；`auto` 简化写法；注意 `end()-1` 反向遍历时的边界。"),
            ("子串匹配", "`find(sub, start)` 从 start 起查找；循环查找可统计出现次数；`npos` 为 size_t 最大值。"),
            ("字典序", "字符串按字符 ASCII 逐位比较；`sort` 可直接对 string 数组排序；大小写敏感，需统一转小写再比。"),
            ("字符串哈希", "将字符串映射为整数：`hash = hash * P + c`，P 常取 131 或 13331；冲突概率低，适合 O(n log n) 去重。"),
            ("字符分类", "数字 0-9、大写 A-Z、小写 a-z 可用 `c-'0'`、`c-'A'`、`c-'a'` 转下标。"),
        ],
        "tips": [
            "find 返回 size_t，与 -1 比较要用 `(int)pos == -1` 或 `pos == string::npos`。",
            "大量字符串拼接用 string 而非 char 数组，避免溢出。",
            "哈希去重后需 sort + unique，或用 set<ull> 存哈希值。",
            "读入含空格的字符串用 getline(cin, s)。",
        ],
        "examples": [
            (
                "string 常用操作（摘自 字符串01.cpp）",
                """string st = "abcd";
st = 'j' + st + "kjh";           // 拼接
st.push_back('X');                 // 尾部追加
st.insert(0, 5, 'P');              // 头部插入 5 个 P
st.pop_back();                     // 删除最后一个字符

ll pos = st.find("abc");           // 查找子串，找不到返回 npos
string sub = st.substr(10, 5);     // 从位置 10 取 5 个字符
st.replace(0, 5, "QQQQQ");         // 替换 [0,5) 为 QQQQQ

// 反向遍历
for (auto it = st.end()-1; it >= st.begin(); it--)
    cout << *it;""",
            ),
            (
                "字符串哈希模板（P3370）",
                """const ull P = 131;
ull hash_str(const string& s) {
    ull res = 0;
    for (char c : s)
        res = res * P + c;
    return res;
}
// 去重：哈希后 sort + unique
vector<ull> a(n);
for (int i = 0; i < n; i++) {
    string s; cin >> s;
    ull h = 0, p = 131;
    for (char c : s) h = h * p + c;
    a[i] = h;
}
sort(a.begin(), a.end());
a.erase(unique(a.begin(), a.end()), a.end());
cout << a.size();  // 不同字符串个数""",
            ),
        ],
        "problems": ["B2118 验证子串", "P3370 字符串哈希", "P10468 兔子与兔子", "P2786 英语单词"],
    },
    {
        "filename": "03_排序分治与二分查找.pdf",
        "title": "第03课：排序、分治与二分查找",
        "subtitle": "归并排序 · 逆序对 · 二分答案 · 二分查找模板",
        "source_files": [
            "排序-归并-P1177排序.cpp", "分治-P1908逆序对.cpp",
            "二分-模板.cpp", "二分-元素首尾位置.cpp", "二分-STL.cpp",
            "二分-查找-P1678烦恼的高考志愿.cpp", "二分-答案-P1873砍树.cpp",
            "二分-答案-P2440木材加工.cpp", "二分-答案-贪心-P2678跳石头.cpp",
        ],
        "objectives": [
            "手写归并排序，理解分治思想",
            "用归并排序求逆序对数量",
            "掌握二分查找左边界/右边界模板",
            "理解二分答案：在答案空间上二分 + 判定函数",
        ],
        "concepts": [
            ("归并排序", "分治：先递归排序左右半段，再合并两个有序区间；时间 O(n log n)，稳定排序。"),
            ("逆序对", "i<j 且 a[i]>a[j] 的对数；归并合并时若左元素大于右元素，则左元素与右半段剩余元素均构成逆序对。"),
            ("二分查找", "在有序数组上找目标；`l+(r-l)/2` 防溢出；左边界：`a[mid]>=x` 则 r=mid；右边界：`a[mid]<=x` 则 l=mid。"),
            ("二分答案", "答案具有单调性时，在 [L,R] 上二分 mid，用 check(mid) 判定是否可行，取最优。"),
            ("STL 二分", "`lower_bound(a, a+n, x)` 返回第一个 >=x 的位置；`upper_bound` 返回第一个 >x 的位置；`binary_search` 判断是否存在。"),
        ],
        "tips": [
            "二分循环条件：找左边界用 `while(l<r)`，找右边界用 `while(l<r)` 且 mid=`l+(r-l+1)/2`。",
            "二分答案的关键是写出正确的 check 函数，并确认答案单调性。",
            "归并排序需额外 O(n) 辅助数组，注意下标从 1 还是从 0 开始。",
            "sort 默认升序；降序用 `greater<T>()` 或 `sort(a.rbegin(), a.rend())`。",
        ],
        "examples": [
            (
                "归并排序模板（P1177）",
                """void merge(ll l, ll r) {
    if (l >= r) return;
    ll mid = l + (r - l) / 2;
    merge(l, mid);          // 排序左半
    merge(mid+1, r);        // 排序右半
    // 合并两个有序区间到临时数组 t
    ll curl = l, curr = mid + 1, i = l;
    while (curl <= mid && curr <= r) {
        if (a[curl] <= a[curr]) t[i++] = a[curl++];
        else t[i++] = a[curr++];
    }
    while (curl <= mid) t[i++] = a[curl++];
    while (curr <= r) t[i++] = a[curr++];
    for (ll j = l; j <= r; j++) a[j] = t[j];
}""",
            ),
            (
                "二分查找左/右边界（二分-模板.cpp）",
                """// 找第一个 >= m 的位置（左边界）
ll l = 0, r = n - 1;
while (l < r) {
    ll mid = l + (r - l) / 2;
    if (a[mid] >= m) r = mid;
    else l = mid + 1;
}
// 找最后一个 <= m 的位置（右边界）
l = 0; r = n - 1;
while (l < r) {
    ll mid = l + (r - l + 1) / 2;  // 注意 +1 防死循环
    if (a[mid] <= m) l = mid;
    else r = mid - 1;
}""",
            ),
        ],
        "problems": ["P1177 排序", "P1908 逆序对", "P1678 烦恼的高考志愿", "P1873 砍树", "P2678 跳石头"],
    },
    {
        "filename": "04_前缀和与差分.pdf",
        "title": "第04课：前缀和与差分",
        "subtitle": "一维/二维前缀和 · 差分数组 · 区间修改与查询",
        "source_files": [
            "前缀和-模板.cpp", "前缀和-二维前缀和.cpp", "前缀和-二维-激光炸弹.cpp",
            "前缀和-最大子段和P1115.cpp", "差分-模板.cpp", "差分-P3406海底高铁.cpp",
            "差分-二维-P3397地毯.cpp", "差分-二维差分模板.cpp",
        ],
        "objectives": [
            "掌握一维前缀和：O(1) 区间求和",
            "掌握二维前缀和：O(1) 子矩阵求和",
            "理解差分数组：O(1) 区间加、最后前缀和还原",
            "应用前缀和解决最大子段和等问题",
        ],
        "concepts": [
            ("一维前缀和", "`dp[i] = a[1]+...+a[i]`，区间 [l,r] 和为 `dp[r]-dp[l-1]`；预处理 O(n)，查询 O(1)。"),
            ("二维前缀和", "`s[i][j]` 表示 (1,1) 到 (i,j) 矩形和；子矩阵 (x1,y1)-(x2,y2) 和 = s[x2][y2]-s[x1-1][y2]-s[x2][y1-1]+s[x1-1][y1-1]。"),
            ("差分", "原数组 a 的差分 d[i]=a[i]-a[i-1]；区间 [l,r] 加 v：d[l]+=v, d[r+1]-=v；最后前缀和还原 a。"),
            ("差分初始化", "读入 a[i] 时：d[i]+=a[i], d[i+1]-=a[i]，等价于对 [i,i] 加 a[i]。"),
            ("最大子段和", "可 DP：`dp[i]=max(a[i], dp[i-1]+a[i])`；或前缀和+最小前缀优化。"),
        ],
        "tips": [
            "前缀和下标通常从 1 开始，dp[0]=0 便于计算。",
            "差分修改区间 [l,r] 时，r+1 可能越界，需保证数组开够大。",
            "二维差分：矩形 (x1,y1)-(x2,y2) 加 v 需改四个角点。",
            "多次区间修改后一次还原，差分比逐个修改高效。",
        ],
        "examples": [
            (
                "一维前缀和模板",
                """cin >> n >> q;
vector<ll> dp(n+1), a(n+1);
for (int i = 1; i <= n; i++) {
    cin >> a[i];
    dp[i] = a[i] + dp[i-1];   // 前缀和
}
while (q--) {
    cin >> lt >> rt;
    ll sum = dp[rt] - dp[lt-1];  // O(1) 区间求和
    cout << sum << '\\n';
}""",
            ),
            (
                "差分数组模板（差分-模板.cpp）",
                """vector<ll> diff(n+2);
// 方法：读入时直接构建差分
for (int i = 1; i <= n; i++) {
    cin >> x;
    diff[i] += x;
    diff[i+1] -= x;
}
// 区间 [lt, rt] 加 k
while (q--) {
    cin >> lt >> rt >> k;
    diff[lt] += k;
    diff[rt+1] -= k;
}
// 前缀和还原原数组
for (int i = 1; i <= n; i++) {
    diff[i] += diff[i-1];
    cout << diff[i] << ' ';
}""",
            ),
        ],
        "problems": ["P1115 最大子段和", "P3406 海底高铁", "P3397 地毯", "激光炸弹"],
    },
    {
        "filename": "05_双指针与滑动窗口.pdf",
        "title": "第05课：双指针与滑动窗口",
        "subtitle": "同向双指针 · 对向双指针 · 滑动窗口 · 无重复最长子串",
        "source_files": [
            "双指针-1.cpp", "双指针-2.cpp", "双指针-滑动窗口-丢手绢.cpp",
            "双指针-字符串-含k个相同字符的最短子段.cpp", "模拟-双指针-找1.cpp",
        ],
        "objectives": [
            "理解同向双指针（快慢指针）维护窗口",
            "掌握滑动窗口模板：进窗口 → 判合法 → 出窗口 → 更新答案",
            "应用双指针解决无重复最长子串、两数之和等问题",
            "理解对向双指针在有序数组上的应用",
        ],
        "concepts": [
            ("同向双指针", "l、r 同向移动，r 扩展窗口，l 收缩窗口；每个元素最多进出各一次，总复杂度 O(n)。"),
            ("滑动窗口", "维护满足条件的连续子区间；用 map/set 记录窗口内元素频次；不合法时 l++ 缩小窗口。"),
            ("对向双指针", "l 从左、r 从右向中间移动；适用于有序数组两数之和、盛水等问题。"),
            ("窗口合法性", "常见条件：无重复元素、元素种类数、和/积约束；用哈希表或数组计数。"),
        ],
        "tips": [
            "滑动窗口经典四步：1.初始化 2.r 进窗口 3.while 不合法 l 出窗口 4.更新 ans。",
            "无重复最长子串：map 记录频次，>1 时 l 右移直到合法。",
            "双指针避免 O(n²) 枚举所有子区间。",
            "注意空窗口、单元素窗口的边界情况。",
        ],
        "examples": [
            (
                "无重复最长子串（双指针-1.cpp）",
                """// 求最长无重复子串长度
unordered_map<int,int> mp;
int ans = 0, l = 1, r = 1;
while (r <= n) {
    mp[a[r]]++;                    // 2. r 进窗口
    while (mp[a[r]] > 1) {          // 3. 不合法则收缩
        mp[a[l]]--;
        l++;
    }
    ans = max(ans, r - l + 1);     // 4. 更新答案
    r++;
}""",
            ),
            (
                "滑动窗口通用模板",
                """int l = 1, r = 1, ans = 0;
while (r <= n) {
    add(a[r]);           // 元素进入窗口
    while (!valid()) {   // 窗口不合法
        remove(a[l]);    // 左端出窗口
        l++;
    }
    ans = max(ans, r - l + 1);  // 或 min，视题意
    r++;
}""",
            ),
        ],
        "problems": ["无重复最长子串", "含 k 个相同字符的最短子段", "丢手绢", "两数之和"],
    },
    {
        "filename": "06_栈队列与单调结构.pdf",
        "title": "第06课：栈、队列与单调结构",
        "subtitle": "栈与括号匹配 · 单调栈 · 单调队列 · 优先队列",
        "source_files": [
            "stack-验证栈序列.cpp", "stack-后缀表达式.cpp", "单调栈-模板.cpp",
            "单调栈-P5788单调栈.cpp", "单调栈-P1901发射站.cpp",
            "单调队列-滑动窗口-模板-P1886.cpp", "优先队列-P1631序列合并.cpp",
        ],
        "objectives": [
            "掌握 stack 后进先出，解决括号匹配、表达式求值",
            "理解单调栈：找左右第一个更大/更小元素",
            "掌握单调队列：滑动窗口最值 O(n)",
            "了解 priority_queue 堆的应用",
        ],
        "concepts": [
            ("栈 stack", "LIFO；push/pop/top；用于括号匹配、DFS 模拟、表达式求值、单调栈。"),
            ("单调栈", "维护单调递增或递减的下标栈；每个元素入栈出栈各一次，O(n)；求下一个更大/更小元素。"),
            ("单调队列", "deque 维护窗口内最值；入队时弹出破坏单调性的队尾；队头为当前窗口最值。"),
            ("优先队列", "priority_queue 默认大根堆；`greater<T>` 为小根堆；用于合并果子、Dijkstra 等。"),
        ],
        "tips": [
            "单调栈存下标而非值，便于计算距离。",
            "单调栈：求左侧第一个更大 → 从左到右，栈单调递减；求右侧第一个更大 → 从右到左。",
            "单调队列：窗口大小 k 时，i-k 位置的元素需从队头弹出。",
            "后缀表达式：遇数字入栈，遇运算符弹出两个运算再入栈。",
        ],
        "examples": [
            (
                "单调栈四模板（单调栈-模板.cpp）",
                """// 左侧第一个更大元素，栈单调递减
for (int i = 1; i <= n; i++) {
    while (!st.empty() && a[st.top()] <= a[i]) st.pop();
    res[i] = st.empty() ? 0 : st.top();
    st.push(i);
}
// 右侧第一个更小：从 n 到 1 遍历，栈单调递增
for (int i = n; i >= 1; i--) {
    while (!st.empty() && a[st.top()] >= a[i]) st.pop();
    res[i] = st.empty() ? 0 : st.top();
    st.push(i);
}""",
            ),
            (
                "单调队列滑动窗口最值（P1886）",
                """deque<ll> dq;
for (int i = 1; i <= n; i++) {
    // 窗口最小值：单调递增，队头为最小
    while (!dq.empty() && a[i] <= a[dq.back()]) dq.pop_back();
    dq.push_back(i);
    if (dq.back() - dq.front() + 1 > k) dq.pop_front();
    if (i >= k) res1[i] = a[dq.front()];
}""",
            ),
        ],
        "problems": ["P5788 单调栈", "P1901 发射站", "P1886 滑动窗口", "P1631 序列合并", "验证栈序列"],
    },
    {
        "filename": "07_递归DFS与回溯.pdf",
        "title": "第07课：递归、DFS 与回溯",
        "subtitle": "全排列 · 组合枚举 · 子集 · N 皇后 · 剪枝优化",
        "source_files": [
            "递归-简单-P1706全排列问题.cpp", "递归-简单-P10448组合型枚举.cpp",
            "递归-简单-B3623排列型枚举.cpp", "dfs-简单-B3622枚举子集.cpp",
            "dfs-N皇后问题-P1219八皇后.cpp", "dfs-组合-可行性剪枝-P1025数的划分.cpp",
            "递归-素数-P1036选数1.cpp", "递归-初阶-汉诺塔.cpp",
        ],
        "objectives": [
            "掌握 DFS 递归三要素：入口、出口、递归体",
            "实现全排列、组合、子集枚举",
            "理解回溯：选择 → 递归 → 恢复现场",
            "应用剪枝减少搜索空间",
        ],
        "concepts": [
            ("递归", "函数调用自身；需明确边界条件（出口）和递推关系；注意栈深度，n 过大可能溢出。"),
            ("回溯", "在决策树上 DFS；做选择前标记，递归返回后撤销标记（恢复现场），尝试其他分支。"),
            ("全排列", "n 个元素排列，用 used 数组标记已选，path 记录当前路径，pos 表示填第几位。"),
            ("组合/子集", "组合从 start 起选，避免重复；子集枚举可用二进制或 DFS 选/不选。"),
            ("剪枝", "提前判断分支不可行则 return，如 N 皇后攻击范围、和超过上限等。"),
        ],
        "tips": [
            "回溯模板：for 选择 → 标记 → dfs(下一层) → 撤销标记。",
            "全排列输出格式注意题目要求（空格、换行、字典序）。",
            "N 皇后可用 attack 数组标记攻击位，或位运算优化。",
            "记忆化 DFS：重复子问题存 dp，如 dfs-记忆化-P1962。",
        ],
        "examples": [
            (
                "全排列 DFS（P1706）",
                """vector<ll> path, used;
void dfs(ll pos) {
    if (pos > n) {              // 出口：填完 n 位
        for (ll x : path) printf("%5lld", x);
        printf("\\n");
        return;
    }
    for (int i = 1; i <= n; i++) {
        if (!used[i]) {
            used[i] = true;
            path.push_back(i);
            dfs(pos + 1);       // 下一层
            path.pop_back();    // 恢复现场
            used[i] = false;
        }
    }
}""",
            ),
            (
                "N 皇后回溯（P1219 核心思路）",
                """// 按行放皇后，attack 标记不可放位置
void dfs(int line, ...) {
    if (line == n) { res.push_back(queen); return; }
    for (int col = 0; col < n; col++) {
        if (attack[line][col] == 0) {
            auto temp = attack;           // 备份
            queen[line][col] = 'Q';
            putqueen(line, col, attack);  // 标记攻击范围
            dfs(line + 1, ...);
            attack = temp;                // 恢复
            queen[line][col] = '.';
        }
    }
}""",
            ),
        ],
        "problems": ["P1706 全排列", "P10448 组合型枚举", "P1219 八皇后", "P1025 数的划分", "P1036 选数", "汉诺塔"],
    },
    {
        "filename": "08_贪心算法.pdf",
        "title": "第08课：贪心算法",
        "subtitle": "活动选择 · 推公式 · 哈夫曼编码 · 简单贪心策略",
        "source_files": [
            "贪心-简单贪心-P1094纪念品分组.cpp", "贪心-简单贪心-P1056排座椅.cpp",
            "贪心-简单贪心-P10452仓库选址.cpp", "贪心-推公式-P1012拼数.cpp",
            "贪心-推公式-P1842奶牛玩杂技.cpp", "贪心-哈夫曼编码-模板.cpp",
            "哈夫曼编码-合并果子-P1090.cpp", "贪心-数学-CF2203B美丽数.cpp",
        ],
        "objectives": [
            "理解贪心：每步局部最优，期望得到全局最优",
            "掌握排序后双指针、相邻配对等贪心策略",
            "学会推公式型贪心（如拼数、奶牛杂技）",
            "了解哈夫曼编码与合并果子",
        ],
        "concepts": [
            ("贪心思想", "每步做当前看起来最优的选择；需证明贪心选择性质和最优子结构。"),
            ("排序贪心", "先 sort，再按某种顺序处理；如纪念品分组：最大+最小配对。"),
            ("推公式", "根据问题性质推导比较规则；如拼数：a+b > b+a 则 a 应在前。"),
            ("哈夫曼", "每次合并最小的两个，用 priority_queue 小根堆；合并代价为两数之和。"),
            ("区间贪心", "按右端点排序选区间；按左端点排序覆盖；活动选择问题经典模型。"),
        ],
        "tips": [
            "贪心不总是正确，需验证或反证；可先写暴力对拍。",
            "纪念品分组：排序后 i 从最大、j 从最小，能配对则 j++。",
            "拼数：`return a+b > b+a` 作为 sort 的比较函数。",
            "哈夫曼：priority_queue<ll, vector<ll>, greater<ll>> 小根堆。",
        ],
        "examples": [
            (
                "纪念品分组（P1094）",
                """sort(a.begin()+1, a.end());
ll sum = 0, i = n, j = 1;
for (; i >= j; i--) {
    if (i == j) { sum++; break; }           // 剩一个单独一组
    if (a[i] + a[j] > w) sum++;             // 最大+最小超重量，最大单独
    else { sum++; j++; }                    // 否则配对
}
cout << sum;""",
            ),
            (
                "哈夫曼合并果子（P1090）",
                """priority_queue<ll, vector<ll>, greater<ll>> pq;
for (int i = 0; i < n; i++) {
    ll x; cin >> x;
    pq.push(x);
}
ll cost = 0;
while (pq.size() > 1) {
    ll a = pq.top(); pq.pop();
    ll b = pq.top(); pq.pop();
    cost += a + b;
    pq.push(a + b);
}
cout << cost;""",
            ),
        ],
        "problems": ["P1094 纪念品分组", "P1056 排座椅", "P10452 仓库选址", "P1012 拼数", "P1090 合并果子"],
    },
    {
        "filename": "09_动态规划.pdf",
        "title": "第09课：动态规划",
        "subtitle": "线性 DP · 数字三角形 · 空间优化 · 最大子段和",
        "source_files": [
            "动态规划-P1216数字三角形.cpp", "动态规划-空间优化-P1216数字三角形2.cpp",
            "前缀和-动态规划-滑动窗口-P1115最大子段和.cpp", "dfs-记忆化-P1962.cpp",
        ],
        "objectives": [
            "理解 DP 三要素：状态、转移方程、初始条件",
            "掌握数字三角形路径最大和",
            "学会滚动数组/空间优化",
            "区分 DP 与记忆化搜索",
        ],
        "concepts": [
            ("动态规划", "将问题分解为重叠子问题，存子问题解避免重复计算；通常按阶段填表。"),
            ("数字三角形", "`dp[i][j] = max(dp[i-1][j-1], dp[i-1][j]) + a[i][j]`；从顶到底或从底到顶均可。"),
            ("空间优化", "若 dp[i] 只依赖 dp[i-1]，可用一维数组滚动：`dp[j] = max(dp[j-1], dp[j]) + a[i][j]`。"),
            ("最大子段和", "`dp[i] = max(a[i], dp[i-1]+a[i])`；或维护 min_prefix 用前缀和优化。"),
            ("记忆化", "DFS + 缓存，如斐波那契；与递推 DP 等价，写法不同。"),
        ],
        "tips": [
            "定义状态要想清楚：dp[i] 或 dp[i][j] 表示什么。",
            "初始化：dp[0][0]=0，不可达状态设为 -INF。",
            "填表顺序：保证计算 dp[i] 时所需子状态已算完。",
            "输出方案：另开 path 数组记录决策，或从终态反推。",
        ],
        "examples": [
            (
                "数字三角形（P1216）",
                """memset(dp, -0x3f, sizeof(dp));
dp[0][0] = dp[0][1] = 0;
for (int i = 1; i <= n; i++)
    for (int j = 1; j <= i; j++)
        cin >> a[i][j];

for (int i = 1; i <= n; i++)
    for (int j = 1; j <= i; j++)
        dp[i][j] = max(dp[i-1][j-1], dp[i-1][j]) + a[i][j];

ll ans = -1e18;
for (int j = 1; j <= n; j++)
    ans = max(ans, dp[n][j]);
cout << ans;""",
            ),
            (
                "最大子段和 DP",
                """// dp[i] = 以 a[i] 结尾的最大子段和
ll dp = 0, ans = -1e18;
for (int i = 1; i <= n; i++) {
    dp = max((ll)a[i], dp + a[i]);
    ans = max(ans, dp);
}
cout << ans;""",
            ),
        ],
        "problems": ["P1216 数字三角形", "P1115 最大子段和", "P1962 斐波那契（记忆化）"],
    },
    {
        "filename": "10_高级数据结构.pdf",
        "title": "第10课：高级数据结构",
        "subtitle": "字典树 Trie · 字符串哈希 · 位运算 · 高精度 · GCD",
        "source_files": [
            "Trie-模板-字P8306典树.cpp", "Trie-P10471最大异或数.cpp",
            "字符串哈希-模板-P3370.cpp", "位运算-&-判断2的幂.cpp",
            "位运算-异或-消失的数.cpp", "高精度-加法.cpp", "高精度-乘法.cpp",
            "gcd-三数gcd.cpp", "倍增-P1226快速幂.cpp", "快速幂-逆元-B2164组合数问题.cpp",
        ],
        "objectives": [
            "掌握 Trie 插入、查询、前缀统计",
            "理解位运算：与或非、异或、lowbit、判断 2 的幂",
            "掌握高精度加减乘除",
            "了解 GCD、快速幂、逆元",
        ],
        "concepts": [
            ("Trie 字典树", "多叉树存字符串；每个节点有 26/62 个子节点；insert 沿路径走，query 判是否存在；pass 记录经过次数，end 记录单词结尾次数。"),
            ("位运算", "`& | ^ ~ << >>`；`n & (n-1)` 清除最低位 1；`n & -n` 取 lowbit；判断 2 的幂：`(n & (n-1)) == 0`。"),
            ("高精度", "用数组存每一位，逆序存储；加减乘逐位运算，注意进位借位。"),
            ("GCD", "欧几里得算法：`gcd(a,b) = gcd(b, a%b)`；扩展 gcd 求逆元。"),
            ("快速幂", "`a^b mod p` 用二进制分解 b，O(log b)；逆元：`a^(p-2) mod p`（p 为质数）。"),
        ],
        "tips": [
            "Trie 字符映射：0-9→0-9，A-Z→10-35，a-z→36-61，共 62 分支。",
            "高精度加法：对齐长度，逐位加，进位；减法需判断大小。",
            "异或：a^a=0，a^0=a；可用于找出现奇数次的数。",
            "快速幂取模：每步乘法后 `% MOD` 防溢出。",
        ],
        "examples": [
            (
                "Trie 插入与前缀查询（P8306）",
                """ll tree[N][62], pass[N], e[N], idx;
ll get_num(char c) {
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'A' && c <= 'Z') return c - 'A' + 10;
    return c - 'a' + 36;
}
void insert_str(string& s) {
    ll cur = 0;
    pass[cur]++;
    for (char c : s) {
        ll p = get_num(c);
        if (!tree[cur][p]) tree[cur][p] = ++idx;
        cur = tree[cur][p];
        pass[cur]++;
    }
    e[cur]++;
}
ll find_pre(string& s) {  // 前缀出现次数
    ll cur = 0;
    for (char c : s) {
        ll p = get_num(c);
        if (!tree[cur][p]) return 0;
        cur = tree[cur][p];
    }
    return pass[cur];
}""",
            ),
            (
                "判断 2 的幂 & 高精度加法",
                """// 位运算：n 是 2 的幂当且仅当 n>0 且 (n & (n-1)) == 0
bool is_pow2(ll n) {
    return n > 0 && (n & (n - 1)) == 0;
}

// 高精度加法：逆序存，逐位加进位
reverse(n1.begin(), n1.end());
reverse(n2.begin(), n2.end());
ll carry = 0;
for (int i = 1; i < len; i++) {
    carry = carry + a[i] + b[i];
    c[i] = carry % 10;
    carry /= 10;
}
if (carry) c.push_back(carry);""",
            ),
        ],
        "problems": ["P8306 字典树", "P10471 最大异或数", "P3370 字符串哈希", "P1226 快速幂", "B2164 组合数"],
    },
]


def build_pdf(course: dict, styles: dict) -> None:
    out_path = OUT_DIR / course["filename"]
    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title=course["title"],
    )
    story: list = []

    story.append(Paragraph(esc(course["title"]), styles["title"]))
    story.append(Paragraph(esc(course["subtitle"]), styles["subtitle"]))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e0")))
    story.append(Spacer(1, 0.3 * cm))

    story.append(section("一、学习目标", styles))
    story.extend(bullets(course["objectives"], styles))
    story.append(Spacer(1, 0.2 * cm))

    story.append(section("二、核心知识点", styles))
    for name, desc in course["concepts"]:
        story.append(Paragraph(f"<b>{esc(name)}</b>：{esc(desc)}", styles["body"]))
    story.append(Spacer(1, 0.2 * cm))

    story.append(section("三、常识与技巧", styles))
    story.extend(bullets(course["tips"], styles))
    story.append(Spacer(1, 0.2 * cm))

    story.append(section("四、参考源码文件", styles))
    story.append(
        Paragraph(
            esc(
                "本课内容整理自竞赛题库文件夹 2026fare，对应源码："
                + "、".join(course["source_files"])
            ),
            styles["body"],
        )
    )
    story.append(Spacer(1, 0.2 * cm))

    story.append(section("五、代码示例与注释", styles))
    for idx, (title, code) in enumerate(course["examples"], 1):
        story.append(Paragraph(esc(f"示例 {idx}：{title}"), styles["code_title"]))
        story.extend(code_block(code, styles))

    story.append(section("六、配套练习题", styles))
    story.extend(bullets(course["problems"], styles))
    story.append(Spacer(1, 0.3 * cm))

    story.append(section("七、本课小结", styles))
    summary = (
        f"本课「{course['title'].split('：', 1)[-1]}」涵盖 "
        f"{len(course['concepts'])} 个核心概念、"
        f"{len(course['examples'])} 段代码示例，"
        f"建议结合 2026fare 文件夹中对应 .cpp 文件动手练习，"
        f"并在 OJ 平台完成配套题目巩固。"
    )
    story.append(Paragraph(esc(summary), styles["body"]))

    doc.build(story)
    print(f"  OK  {out_path.name}  ({out_path.stat().st_size:,} bytes)")


def main() -> None:
    register_fonts()
    styles = build_styles()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Output: {OUT_DIR}")
    print(f"Generating {len(COURSES)} course PDFs...")
    for course in COURSES:
        build_pdf(course, styles)
    print("Done.")


if __name__ == "__main__":
    main()

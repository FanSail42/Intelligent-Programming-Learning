"""Seed 50 programming courses (C/C++/Java/Python). Safe to run multiple times."""
import os
import sys
from datetime import datetime, timedelta

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.insert(0, BACKEND_DIR)
os.chdir(BACKEND_DIR)

from app.core.database import SessionLocal
from app.models.course import (
    Course,
    CourseCreateApproval,
    CoursePublishApproval,
    CourseStatus,
    CourseTeacher,
)
from app.models.user import User, UserRole, UserStatus

# (name, description, language_tag, status, create_approval, publish_approval, days_ago_published)
COURSE_SEED_DATA: list[tuple] = [
    ("Python 异步编程与 asyncio 实战", "掌握协程、事件循环与 aiohttp 高并发 Web 客户端开发。", "Python", "published", "approved", "approved", 120),
    ("Python 数据分析入门：Pandas 与 NumPy", "从数据清洗、透视表到可视化，完成完整数据分析闭环。", "Python", "published", "approved", "approved", 115),
    ("Python Web 开发：FastAPI 微服务", "RESTful API、依赖注入、JWT 鉴权与 OpenAPI 文档自动生成。", "Python", "published", "approved", "approved", 110),
    ("Python 机器学习基础：Scikit-learn", "线性回归、决策树、聚类与模型评估的动手实验课。", "Python", "published", "approved", "approved", 105),
    ("Python 自动化运维脚本编写", "使用 pathlib、subprocess 与 schedule 实现巡检与部署自动化。", "Python", "published", "approved", "approved", 100),
    ("Python 爬虫与反爬策略", "Requests、BeautifulSoup、Playwright 与 IP 代理池实战。", "Python", "published", "approved", "approved", 95),
    ("Python 游戏开发：Pygame 入门", "精灵动画、碰撞检测与关卡设计，完成横版小游戏。", "Python", "draft", "approved", "none", None),
    ("Python 深度学习：PyTorch 神经网络", "张量运算、自动求导、CNN 与迁移学习项目。", "Python", "published", "approved", "approved", 90),
    ("Python 函数式编程范式", "map/filter/reduce、闭包、装饰器与高阶函数设计。", "Python", "published", "approved", "approved", 85),
    ("Python 类型标注与 mypy 静态检查", "TypedDict、Protocol、泛型与大型项目类型治理。", "Python", "draft", "pending", "none", None),
    ("Python 并发编程：多线程与多进程", "GIL、线程池、进程池与 Queue 生产者消费者模型。", "Python", "published", "approved", "approved", 80),
    ("Python 科学计算：SymPy 符号运算", "符号求导、方程求解与 LaTeX 公式输出。", "Python", "published", "approved", "approved", 75),
    ("Python DSL 设计与元编程", "AST 改写、装饰器 DSL 与插件化框架设计。", "Python", "archived", "approved", "approved", 200),
    ("Java 面向对象程序设计核心", "封装、继承、多态与抽象类接口的系统讲解。", "Java", "published", "approved", "approved", 118),
    ("Java Spring Boot 企业级开发", "Controller-Service-Repository 分层与 MyBatis 集成。", "Java", "published", "approved", "approved", 112),
    ("Java 多线程与并发编程", "synchronized、Lock、线程池与并发容器源码导读。", "Java", "published", "approved", "approved", 108),
    ("Java 虚拟机 JVM 原理与调优", "类加载、垃圾回收、内存模型与 GC 日志分析。", "Java", "published", "approved", "approved", 102),
    ("Java 设计模式实战", "单例、工厂、观察者、策略模式在业务中的落地。", "Java", "published", "approved", "approved", 98),
    ("Java 微服务架构：Spring Cloud", "Nacos、Gateway、Feign 与分布式链路追踪。", "Java", "published", "approved", "approved", 92),
    ("Java 集合框架深度解析", "ArrayList、HashMap、ConcurrentHashMap 底层实现。", "Java", "draft", "approved", "none", None),
    ("Java 函数式接口与 Stream API", "Lambda、Optional 与流式数据处理最佳实践。", "Java", "published", "approved", "approved", 88),
    ("Java Android 移动开发入门", "Activity 生命周期、RecyclerView 与 Material 组件。", "Java", "published", "approved", "approved", 82),
    ("Java 网络编程与 NIO", "BIO/NIO/AIO 对比、Selector 与 Netty 入门。", "Java", "published", "approved", "approved", 78),
    ("Java 单元测试：JUnit 5 与 Mockito", "参数化测试、Mock 隔离与测试覆盖率驱动开发。", "Java", "draft", "pending", "none", None),
    ("Java 安全编程与常见漏洞防护", "SQL 注入、XSS、CSRF 与 OWASP Top 10 防护。", "Java", "published", "approved", "approved", 72),
    ("Java 响应式编程：Project Reactor", "Mono/Flux、背压与响应式 WebFlux 接口。", "Java", "archived", "approved", "approved", 180),
    ("C 语言程序设计基础", "变量、控制流、函数与数组，建立结构化编程思维。", "C", "published", "approved", "approved", 116),
    ("C 语言指针与内存管理", "指针算术、动态分配、内存泄漏排查与 Valgrind。", "C", "published", "approved", "approved", 111),
    ("C 语言数据结构实现", "手写链表、栈、队列、二叉树与哈希表。", "C", "published", "approved", "approved", 106),
    ("C 语言系统编程入门", "进程、信号、管道与 fork/exec 系统调用。", "C", "published", "approved", "approved", 101),
    ("C 语言嵌入式开发实战", "GPIO、UART、中断与 STM32 HAL 库编程。", "C", "published", "approved", "approved", 96),
    ("C 语言网络编程：Socket", "TCP/UDP 通信、select 多路复用与简易 HTTP 服务器。", "C", "published", "approved", "approved", 91),
    ("C 语言算法竞赛训练", "贪心、动态规划、图论与 STL 风格手写模板。", "C", "draft", "approved", "none", None),
    ("C 语言位运算与底层优化", "掩码技巧、位域、缓存友好与 SIMD 初步。", "C", "published", "approved", "approved", 86),
    ("C 语言文件 IO 与序列化", "fopen/fread、二进制协议与 CRC 校验。", "C", "published", "approved", "approved", 81),
    ("C 语言多文件项目组织", "头文件守卫、Makefile 与静态/动态库链接。", "C", "draft", "pending", "none", None),
    ("C 语言与操作系统接口", "POSIX API、errno 处理与跨平台移植。", "C", "published", "approved", "approved", 76),
    ("C 语言编译原理初探", "词法分析、递归下降解析与简易解释器实现。", "C", "archived", "approved", "approved", 190),
    ("C++ 面向对象编程进阶", "虚函数、多重继承、RTTI 与面向对象设计原则。", "C++", "published", "approved", "approved", 114),
    ("C++ STL 标准模板库精通", "vector、map、unordered_map 与迭代器失效规则。", "C++", "published", "approved", "approved", 109),
    ("C++11/14/17 现代特性详解", "auto、lambda、constexpr 与 structured binding。", "C++", "published", "approved", "approved", 104),
    ("C++ 模板元编程入门", "SFINAE、type_traits 与编译期计算。", "C++", "published", "approved", "approved", 99),
    ("C++ 智能指针与 RAII 资源管理", "unique_ptr、shared_ptr、weak_ptr 与自定义删除器。", "C++", "published", "approved", "approved", 94),
    ("C++ 多线程编程：std::thread", "mutex、condition_variable 与 atomic 无锁编程。", "C++", "published", "approved", "approved", 89),
    ("C++ 游戏引擎开发基础", "渲染循环、ECS 架构与物理碰撞初步。", "C++", "draft", "approved", "none", None),
    ("C++ 性能优化与 profiling", "CPU 缓存、分支预测、gprof 与 perf 工具。", "C++", "published", "approved", "approved", 84),
    ("C++ Qt 跨平台 GUI 开发", "信号槽、Model/View 与 QML 界面设计。", "C++", "published", "approved", "approved", 79),
    ("C++ 异常安全与错误处理", "RAII、noexcept 与强异常安全保证。", "C++", "published", "approved", "approved", 74),
    ("C++ 移动语义与完美转发", "右值引用、std::move 与万能引用折叠规则。", "C++", "draft", "pending", "none", None),
    ("C++ 网络库 Boost.Asio 实战", "异步 IO、协程封装与高并发服务端。", "C++", "published", "approved", "approved", 70),
]


def _get_teachers(db) -> list[User]:
    teachers = (
        db.query(User)
        .filter(User.role == UserRole.teacher, User.status == UserStatus.active, User.deleted == 0)
        .order_by(User.id)
        .all()
    )
    if not teachers:
        raise RuntimeError("未找到可用教师账号，请先运行 seed_demo.py 创建 teacher 用户")
    return teachers


def seed_courses() -> None:
    db = SessionLocal()
    try:
        teachers = _get_teachers(db)
        existing_names = {
            name
            for (name,) in db.query(Course.name).filter(Course.deleted == 0).all()
        }

        created = 0
        skipped = 0
        now = datetime.now()

        for idx, row in enumerate(COURSE_SEED_DATA):
            name, description, _lang, status, create_ap, publish_ap, days_ago = row
            if name in existing_names:
                skipped += 1
                continue

            teacher = teachers[idx % len(teachers)]
            status_enum = CourseStatus(status)
            create_enum = CourseCreateApproval(create_ap)
            publish_enum = CoursePublishApproval(publish_ap)
            published_at = None
            if status_enum == CourseStatus.published and days_ago is not None:
                published_at = now - timedelta(days=days_ago, hours=idx % 12, minutes=(idx * 7) % 60)
            elif status_enum == CourseStatus.archived and days_ago is not None:
                published_at = now - timedelta(days=days_ago)

            course = Course(
                name=name,
                description=description,
                teacher_id=teacher.id,
                status=status_enum,
                create_approval=create_enum,
                publish_approval=publish_enum,
                published_at=published_at,
            )
            db.add(course)
            db.flush()
            db.add(CourseTeacher(course_id=course.id, user_id=teacher.id))
            existing_names.add(name)
            created += 1

        db.commit()
        print(f"Course seed done: created={created}, skipped={skipped}, total_in_script={len(COURSE_SEED_DATA)}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_courses()

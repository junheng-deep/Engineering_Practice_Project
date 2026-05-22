import os

JWC_URL = "https://jwc.cuit.edu.cn"
JWGL_URL = "http://jwgl.cuit.edu.cn/eams"
CAS_URL = "https://sso.cuit.edu.cn"

# 调试模式
DEBUG = True

if DEBUG:
    STUDENT_ID = "xxx" # 账号
    PASSWORD = "xxx" # 密码
else:
    STUDENT_ID = os.getenv("STUDENT_ID", "")
    PASSWORD = os.getenv("PASSWORD", "")
#!/bin/bash
# 请在这里将 "学号" 和 "姓名" 替换为您自己的真实信息
STUDENT_ID="2403080546"
STUDENT_NAME="王超浩"

# 最终打包的压缩包名称
PACKAGE_NAME="${STUDENT_ID}${STUDENT_NAME}.zip"

echo "开始打包作业..."
# 排除掉虚拟环境、缓存文件、.env 文件以及可能存在的压缩包本身，防止信息泄漏和死循环
zip -r $PACKAGE_NAME . -x "*/__pycache__/*" "*/.venv/*" "venv/*" ".env" "*.zip" "*.rar" ".git/*"

echo "==================================="
echo "打包完成！最终文件为: $PACKAGE_NAME"
echo "您可以将其提交至 '001Homework1' 下。"
echo "源代码和项目文件已被完整保留在当前目录。"

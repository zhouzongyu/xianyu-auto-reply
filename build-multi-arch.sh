#!/bin/bash
# 多架构 Docker 镜像构建脚本 (AMD64 + ARM64)
# 支持推送到镜像仓库或保存到本地

set -e

echo "========================================"
echo "  多架构 Docker 镜像构建脚本"
echo "========================================"
echo

# 设置镜像标签（可根据需要修改）
IMAGE_NAME="xianyu-replay-fixed"
IMAGE_TAG="latest"
DOCKERFILE="Dockerfile-cn"

# 检查是否要推送到仓库
read -p "是否推送到镜像仓库？(y/n，默认n): " PUSH_IMAGE
PUSH_IMAGE=${PUSH_IMAGE:-n}

if [ "$PUSH_IMAGE" = "y" ] || [ "$PUSH_IMAGE" = "Y" ]; then
    read -p "请输入镜像仓库地址（如：registry.cn-shanghai.aliyuncs.com/your-namespace）: " REGISTRY
    # 去除开头和结尾的斜杠
    REGISTRY=$(echo "$REGISTRY" | sed 's:^/*::' | sed 's:/*$::')
    FULL_IMAGE_NAME="${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
    PUSH_FLAG="--push"
    echo "将推送到: $FULL_IMAGE_NAME"
else
    FULL_IMAGE_NAME="${IMAGE_NAME}:${IMAGE_TAG}"
    PUSH_FLAG=""
    echo "将构建到本地，不推送"
fi

echo
echo "========================================"
echo "步骤 1: 检查 Docker 服务"
echo "========================================"
if ! docker ps >/dev/null 2>&1; then
    echo "[错误] Docker 服务未运行，请先启动 Docker"
    exit 1
fi
echo "[✓] Docker 服务正常运行"

echo
echo "========================================"
echo "步骤 1.5: 基础镜像源配置（解决网络问题）"
echo "========================================"
echo "由于网络连接问题，请选择基础镜像源："
echo "1. 腾讯云镜像 (推荐，国内访问快)"
echo "2. 阿里云镜像"  
echo "3. 中科大镜像"
echo "4. Docker Hub (国外，可能较慢)"
echo
read -p "请选择基础镜像源 (1/2/3/4，默认1): " MIRROR_CHOICE
MIRROR_CHOICE=${MIRROR_CHOICE:-1}

case $MIRROR_CHOICE in
    1)
        BASE_IMAGE="ccr.ccs.tencentyun.com/dockerp/library/python:3.11-slim-bookworm"
        echo "使用腾讯云镜像源"
        ;;
    2)
        BASE_IMAGE="registry.cn-hangzhou.aliyuncs.com/dockerp/library/python:3.11-slim-bookworm"
        echo "使用阿里云镜像源"
        ;;
    3)
        BASE_IMAGE="docker.mirrors.ustc.edu.cn/library/python:3.11-slim-bookworm"
        echo "使用中科大镜像源"
        ;;
    4)
        BASE_IMAGE="docker.1panel.live/library/python:3.11-slim-bookworm"
        echo "使用 Docker Hub 镜像源"
        ;;
    *)
        BASE_IMAGE="ccr.ccs.tencentyun.com/dockerp/library/python:3.11-slim-bookworm"
        echo "使用默认腾讯云镜像源"
        ;;
esac

BASE_IMAGE_ARG="--build-arg BASE_IMAGE=$BASE_IMAGE"
echo "基础镜像: $BASE_IMAGE"
echo

echo
echo "========================================"
echo "步骤 2: 安装 QEMU 模拟器（支持 ARM64）"
echo "========================================"
echo "检查 QEMU 是否已安装..."
if docker run --rm --privileged tonistiigi/binfmt --version >/dev/null 2>&1; then
    echo "安装/更新 QEMU 模拟器..."
    docker run --rm --privileged tonistiigi/binfmt --install all
    if [ $? -eq 0 ]; then
        echo "[✓] QEMU 模拟器安装成功"
    else
        echo "[⚠] QEMU 模拟器安装失败，但可以继续尝试构建"
    fi
else
    echo "[⚠] 无法安装 QEMU 模拟器，ARM64 构建可能需要其他方式"
    echo "    提示：可以在 Linux ARM64 机器上构建，或使用 CI/CD 服务"
fi

echo
echo "========================================"
echo "步骤 3: 检查并创建 buildx builder"
echo "========================================"
if ! docker buildx inspect multiarch-builder >/dev/null 2>&1; then
    echo "创建新的 buildx builder（支持多架构）..."
    # 使用 docker-container driver 以支持多架构
    docker buildx create --name multiarch-builder --driver docker-container --use --bootstrap --driver-opt network=host
    if [ $? -ne 0 ]; then
        echo "[错误] 创建 buildx builder 失败"
        echo "尝试使用默认 driver..."
        docker buildx create --name multiarch-builder --use --bootstrap
        if [ $? -ne 0 ]; then
            echo "[错误] 创建 buildx builder 失败"
            exit 1
        fi
    fi
    echo "[✓] buildx builder 创建成功"
else
    echo "使用现有的 buildx builder"
    docker buildx use multiarch-builder
    docker buildx inspect --bootstrap >/dev/null 2>&1
    echo "[✓] buildx builder 已就绪"
fi

echo
echo "========================================"
echo "步骤 4: 查看支持的平台"
echo "========================================"
PLATFORMS=$(docker buildx inspect --bootstrap | grep "Platforms:" | sed 's/Platforms://' | xargs)
echo "支持的平台: $PLATFORMS"
echo

# 检查是否支持 ARM64
if echo "$PLATFORMS" | grep -q "linux/arm64"; then
    echo "[✓] 检测到 ARM64 支持"
    SUPPORT_ARM64=true
else
    echo "[⚠] 未检测到 ARM64 支持"
    echo "    可能的原因："
    echo "    1. QEMU 模拟器未正确安装"
    echo "    2. Docker Desktop 需要重启"
    echo "    3. 系统不支持模拟（建议在 Linux ARM64 机器上构建）"
    echo ""
    read -p "是否继续构建（将只构建 AMD64 平台）？(y/n): " CONTINUE
    if [ "$CONTINUE" != "y" ] && [ "$CONTINUE" != "Y" ]; then
        echo "已取消构建"
        exit 0
    fi
    SUPPORT_ARM64=false
fi
echo

echo "========================================"
echo "步骤 5: 开始构建镜像"
echo "========================================"
echo "镜像名称: $FULL_IMAGE_NAME"
echo "Dockerfile: $DOCKERFILE"
echo "基础镜像: $BASE_IMAGE"

# 根据 ARM64 支持情况选择平台
if [ "$SUPPORT_ARM64" = "true" ]; then
    PLATFORMS="linux/amd64,linux/arm64"
    echo "平台: $PLATFORMS (多架构)"
else
    PLATFORMS="linux/amd64"
    echo "平台: $PLATFORMS (仅 AMD64，ARM64 不支持)"
fi
echo

if [ -z "$PUSH_FLAG" ]; then
    echo "[注意] 本地构建多架构镜像需要先加载到 Docker，使用 --load 参数"
    echo "[警告] --load 只能加载单个平台，多架构镜像需要推送到仓库"
    echo
    read -p "继续构建单个平台 (amd64) 到本地？(y/n): " CONFIRM
    if [ "$CONFIRM" = "y" ] || [ "$CONFIRM" = "Y" ]; then
        echo "开始构建 AMD64 平台..."
        docker buildx build --platform linux/amd64 -t "$FULL_IMAGE_NAME" -f "$DOCKERFILE" . --load $BASE_IMAGE_ARG
        if [ $? -ne 0 ]; then
            echo ""
            echo "[错误] 构建失败"
            echo "[提示] 如果是网络超时问题，请尝试选择其他国内镜像源"
            exit 1
        fi
    else
        echo "已取消构建"
        exit 0
    fi
else
    if [ "$SUPPORT_ARM64" = "true" ]; then
        echo "========================================"
        echo "构建方式选择"
        echo "========================================"
        echo "1. 同时构建多架构（快速，但可能网络超时）"
        echo "2. 分别构建每个架构（推荐，避免网络问题）"
        echo
        read -p "请选择构建方式 (1/2，默认2): " BUILD_MODE
        BUILD_MODE=${BUILD_MODE:-2}
        
        if [ "$BUILD_MODE" = "1" ]; then
            echo "开始同时构建多架构镜像并推送到仓库..."
            echo "[提示] ARM64 构建使用 QEMU 模拟，速度较慢，请耐心等待..."
            docker buildx build --platform "$PLATFORMS" -t "$FULL_IMAGE_NAME" -f "$DOCKERFILE" . $PUSH_FLAG $BASE_IMAGE_ARG
            if [ $? -ne 0 ]; then
                echo ""
                echo "[错误] 构建失败"
                echo "[提示] 如果是网络问题，请选择方式2（分别构建）或更换镜像源"
                exit 1
            fi
        else
            echo "开始分别构建每个架构..."
            echo ""
            
            # 定义平台标签
            AMD64_TAG="${FULL_IMAGE_NAME}-amd64"
            ARM64_TAG="${FULL_IMAGE_NAME}-arm64"
            
            # 步骤1: 构建 AMD64
            echo "========================================"
            echo "步骤 1: 构建 AMD64 平台"
            echo "========================================"
            echo "镜像标签: $AMD64_TAG"
            docker buildx build --platform linux/amd64 -t "$AMD64_TAG" -f "$DOCKERFILE" . $PUSH_FLAG $BASE_IMAGE_ARG
            if [ $? -ne 0 ]; then
                echo ""
                echo "[错误] AMD64 构建失败"
                echo "[提示] 如果是网络问题，请尝试选择其他国内镜像源"
                exit 1
            fi
            echo "[✓] AMD64 构建完成"
            echo ""
            
            # 步骤2: 构建 ARM64
            echo "========================================"
            echo "步骤 2: 构建 ARM64 平台"
            echo "========================================"
            echo "镜像标签: $ARM64_TAG"
            echo "[提示] ARM64 构建使用 QEMU 模拟，速度较慢，请耐心等待..."
            docker buildx build --platform linux/arm64 -t "$ARM64_TAG" -f "$DOCKERFILE" . $PUSH_FLAG $BASE_IMAGE_ARG
            if [ $? -ne 0 ]; then
                echo ""
                echo "[错误] ARM64 构建失败"
                echo "[提示] 如果是网络问题，请尝试选择其他国内镜像源"
                exit 1
            fi
            echo "[✓] ARM64 构建完成"
            echo ""
            
            # 步骤3: 创建多架构 manifest
            echo "========================================"
            echo "步骤 3: 创建多架构 manifest"
            echo "========================================"
            echo "合并 AMD64 和 ARM64 镜像为多架构镜像: $FULL_IMAGE_NAME"
            
            # 删除已存在的 manifest（如果存在）
            docker manifest rm "$FULL_IMAGE_NAME" 2>/dev/null || true
            
            # 创建新的 manifest
            docker manifest create "$FULL_IMAGE_NAME" "$AMD64_TAG" "$ARM64_TAG"
            if [ $? -ne 0 ]; then
                echo "[错误] 创建 manifest 失败"
                exit 1
            fi
            echo "[✓] Manifest 创建成功"
            
            # 推送 manifest
            docker manifest push "$FULL_IMAGE_NAME"
            if [ $? -ne 0 ]; then
                echo "[错误] 推送 manifest 失败"
                exit 1
            fi
            echo "[✓] 多架构镜像推送完成"
            echo ""
            echo "[提示] 多架构镜像已创建: $FULL_IMAGE_NAME"
            echo "       - AMD64: $AMD64_TAG"
            echo "       - ARM64: $ARM64_TAG"
        fi
    else
        echo "[警告] 当前环境不支持 ARM64，只构建 AMD64 平台"
        echo "开始构建 AMD64 镜像并推送到仓库..."
        docker buildx build --platform linux/amd64 -t "$FULL_IMAGE_NAME" -f "$DOCKERFILE" . $PUSH_FLAG $BASE_IMAGE_ARG
        if [ $? -ne 0 ]; then
            echo ""
            echo "[错误] 构建失败"
            echo "[提示] 如果是网络问题，请尝试选择其他国内镜像源"
            exit 1
        fi
        echo ""
        echo "[建议] 要支持 ARM64，请："
        echo "  1. 在 Linux ARM64 机器上构建 ARM64 镜像"
        echo "  2. 使用 CI/CD 服务（如 GitHub Actions）"
        echo "  3. 或使用云服务器构建"
    fi
fi

echo
echo "========================================"
echo "构建完成！"
echo "========================================"
if [ -z "$PUSH_FLAG" ]; then
    echo "镜像已构建到本地: $FULL_IMAGE_NAME"
    echo
    echo "使用方法:"
    echo "  docker run -d -p 8080:8080 --name xianyu-auto-reply $FULL_IMAGE_NAME"
else
    if [ "$SUPPORT_ARM64" = "true" ] && [ "$BUILD_MODE" = "2" ]; then
        echo "多架构镜像已创建并推送到: $FULL_IMAGE_NAME"
        echo
        echo "镜像组成:"
        echo "  - AMD64: ${FULL_IMAGE_NAME}-amd64"
        echo "  - ARM64: ${FULL_IMAGE_NAME}-arm64"
        echo "  - 多架构: $FULL_IMAGE_NAME"
    else
        echo "镜像已推送到: $FULL_IMAGE_NAME"
    fi
    echo
    echo "使用方法:"
    echo "  docker run -d -p 8080:8080 --name xianyu-auto-reply $FULL_IMAGE_NAME"
    echo
    echo "或者从仓库拉取:"
    echo "  docker pull $FULL_IMAGE_NAME"
    echo
    echo "验证多架构镜像:"
    echo "  docker buildx imagetools inspect $FULL_IMAGE_NAME"
fi

echo
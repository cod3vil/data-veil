#!/bin/bash

# 数据脱敏平台 - 管理脚本
# 支持：部署、启动、停止、重启、日志、状态、清理

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 确定 docker compose 命令
if docker compose version &> /dev/null 2>&1; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

# 打印横幅
print_banner() {
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}数据脱敏平台管理工具${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
}

# 检查前置条件
check_prerequisites() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}错误：未安装 Docker${NC}"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        echo -e "${RED}错误：未安装 Docker Compose${NC}"
        exit 1
    fi
}

# 部署（构建并启动）
deploy() {
    print_banner
    echo -e "${YELLOW}开始部署...${NC}\n"
    
    check_prerequisites
    
    echo -e "${BLUE}[1/5] 创建必要目录...${NC}"
    mkdir -p uploads models
    echo -e "${GREEN}✓ 完成${NC}\n"
    
    echo -e "${BLUE}[2/5] 检查数据库连接...${NC}"
    if command -v psql &> /dev/null; then
        if PGPASSWORD=2AW5sPDYmZP7sFJS psql -h 172.17.0.1 -U data_veil -d data_veil -c "SELECT 1;" &> /dev/null; then
            echo -e "${GREEN}✓ 数据库连接成功${NC}\n"
        else
            echo -e "${YELLOW}⚠ 无法连接到数据库${NC}"
            echo -e "${YELLOW}  请确保 PostgreSQL 运行在 172.17.0.1:5432${NC}\n"
        fi
    else
        echo -e "${YELLOW}⚠ 未找到 psql，跳过检查${NC}\n"
    fi
    
    echo -e "${BLUE}[3/5] 停止现有容器...${NC}"
    $DOCKER_COMPOSE down 2>/dev/null || true
    echo -e "${GREEN}✓ 完成${NC}\n"
    
    echo -e "${BLUE}[4/5] 构建镜像...${NC}"
    $DOCKER_COMPOSE build --no-cache
    echo -e "${GREEN}✓ 完成${NC}\n"
    
    echo -e "${BLUE}[5/5] 启动服务...${NC}"
    $DOCKER_COMPOSE up -d
    echo -e "${GREEN}✓ 完成${NC}\n"
    
    echo -e "${YELLOW}等待服务启动...${NC}"
    sleep 5
    
    show_status
    show_urls
}

# 启动服务
start() {
    print_banner
    echo -e "${YELLOW}启动服务...${NC}\n"
    
    check_prerequisites
    $DOCKER_COMPOSE up -d
    
    echo -e "${GREEN}✓ 服务已启动${NC}\n"
    show_status
    show_urls
}

# 停止服务
stop() {
    print_banner
    echo -e "${YELLOW}停止服务...${NC}\n"
    
    $DOCKER_COMPOSE stop
    
    echo -e "${GREEN}✓ 服务已停止${NC}\n"
}

# 重启服务
restart() {
    print_banner
    echo -e "${YELLOW}重启服务...${NC}\n"
    
    $DOCKER_COMPOSE restart
    
    echo -e "${GREEN}✓ 服务已重启${NC}\n"
    show_status
}

# 查看日志
logs() {
    SERVICE=$1
    if [ -z "$SERVICE" ]; then
        echo -e "${YELLOW}显示所有日志（按 Ctrl+C 退出）...${NC}\n"
        $DOCKER_COMPOSE logs -f
    else
        echo -e "${YELLOW}显示 $SERVICE 日志（按 Ctrl+C 退出）...${NC}\n"
        $DOCKER_COMPOSE logs -f $SERVICE
    fi
}

# 显示状态
show_status() {
    echo -e "${BLUE}服务状态：${NC}"
    $DOCKER_COMPOSE ps
    echo ""
}

# 显示访问地址
show_urls() {
    echo -e "${GREEN}访问地址：${NC}"
    echo -e "  前端界面：  ${GREEN}http://localhost:8000${NC}"
    echo -e "  后端 API：  ${GREEN}http://localhost:8001${NC}"
    echo -e "  API 文档：  ${GREEN}http://localhost:8001/docs${NC}"
    echo ""
}

# 清理（删除容器、卷、镜像）
clean() {
    print_banner
    echo -e "${RED}警告：此操作将删除所有容器、卷和镜像！${NC}"
    read -p "确定要继续吗？(yes/no): " confirm
    
    if [ "$confirm" = "yes" ]; then
        echo -e "${YELLOW}清理中...${NC}\n"
        $DOCKER_COMPOSE down -v --rmi all
        echo -e "${GREEN}✓ 清理完成${NC}\n"
    else
        echo -e "${YELLOW}已取消清理${NC}\n"
    fi
}

# 显示帮助
show_help() {
    print_banner
    echo -e "${BLUE}用法：${NC}"
    echo -e "  ./deploy.sh [命令] [选项]\n"
    
    echo -e "${BLUE}命令：${NC}"
    echo -e "  ${GREEN}deploy${NC}          构建并启动所有服务"
    echo -e "  ${GREEN}start${NC}           启动现有服务"
    echo -e "  ${GREEN}stop${NC}            停止所有服务"
    echo -e "  ${GREEN}restart${NC}         重启所有服务"
    echo -e "  ${GREEN}status${NC}          显示服务状态"
    echo -e "  ${GREEN}logs${NC} [服务名]   查看日志（所有或指定服务）"
    echo -e "  ${GREEN}clean${NC}           删除所有容器、卷和镜像"
    echo -e "  ${GREEN}help${NC}            显示此帮助信息\n"
    
    echo -e "${BLUE}示例：${NC}"
    echo -e "  ./deploy.sh deploy          # 完整部署"
    echo -e "  ./deploy.sh start           # 启动服务"
    echo -e "  ./deploy.sh logs            # 查看所有日志"
    echo -e "  ./deploy.sh logs backend    # 仅查看后端日志"
    echo -e "  ./deploy.sh logs frontend   # 仅查看前端日志"
    echo ""
}

# 主脚本逻辑
case "$1" in
    deploy)
        deploy
        ;;
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    status)
        print_banner
        show_status
        show_urls
        ;;
    logs)
        logs $2
        ;;
    clean)
        clean
        ;;
    help|--help|-h|"")
        show_help
        ;;
    *)
        echo -e "${RED}错误：未知命令 '$1'${NC}\n"
        show_help
        exit 1
        ;;
esac

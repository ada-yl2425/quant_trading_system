#!/bin/bash

# 修复分支内容脚本
# 这个脚本会修复各个分支的文件内容

set -e

echo "🔧 开始修复分支内容..."
echo "=============================================="

# 检查当前状态
echo "当前分支: $(git branch --show-current)"
echo "未跟踪的文件:"
git status --porcelain

# 确保在main分支，并且所有文件都已提交
git checkout main

# 检查main分支是否有所有文件
if [ ! -f "config.py" ] || [ ! -f "data_loader.py" ] || [ ! -f "feature_processor.py" ] || [ ! -f "signal_builder.py" ] || [ ! -f "backtester.py" ] || [ ! -f "main.py" ] || [ ! -f "README.md" ]; then
    echo "❌ 错误: main分支缺少必要的文件"
    echo "请确保所有文件都在main分支中并已提交"
    exit 1
fi

# 添加并提交未跟踪的文件
if [ -d ".github" ]; then
    git add .github/
    git commit -m "chore: add github templates" || true
fi

if [ -f "git_push_steps.sh" ]; then
    git add git_push_steps.sh
    git commit -m "chore: add deployment script" || true
fi

# 推送到main
git push origin main

echo ""
echo "📋 开始修复各个功能分支..."

# 函数：修复分支内容
fix_branch() {
    local branch_name=$1
    local files=$2
    local commit_msg=$3
    
    echo ""
    echo "修复分支: $branch_name"
    
    # 切换到分支
    git checkout $branch_name
    
    # 重置为main分支的状态
    git reset --hard main
    
    # 删除所有文件，然后只添加指定的文件
    git rm -rf . > /dev/null 2>&1 || true
    
    # 从main恢复指定的文件
    for file in $files; do
        if [ -e "../$file" ]; then
            git checkout main -- "$file"
        fi
    done
    
    # 提交更改
    git add .
    git commit -m "$commit_msg" || true
    
    # 强制推送到远程
    git push origin $branch_name --force
    
    echo "✅ $branch_name 修复完成"
}

# 修复各个分支
fix_branch "base-infrastructure" "config.py requirements.txt .gitignore" "feat: add base configuration and dependencies"
fix_branch "data-loader" "data_loader.py" "feat: implement data loading and cleaning modules" 
fix_branch "feature-processor" "feature_processor.py" "feat: implement feature engineering and selection modules"
fix_branch "signal-builder" "signal_builder.py" "feat: implement online learning model and portfolio management"
fix_branch "backtester" "backtester.py" "feat: implement enhanced backtesting engine"
fix_branch "main-program" "main.py" "feat: implement main program with complete pipeline"
fix_branch "documentation" "README.md" "docs: add comprehensive project documentation"

# 修复dataset-structure分支
echo ""
echo "修复分支: dataset-structure"
git checkout dataset-structure
git reset --hard main
git rm -rf . > /dev/null 2>&1 || true
mkdir -p dataset/raw_data dataset/processed_data output/csv_results output/charts
touch dataset/raw_data/.gitkeep dataset/processed_data/.gitkeep output/csv_results/.gitkeep output/charts/.gitkeep
git add dataset/ output/
git commit -m "feat: add dataset and output directory structure" || true
git push origin dataset-structure --force
echo "✅ dataset-structure 修复完成"

# 回到main分支
git checkout main

echo ""
echo "=============================================="
echo "✅ 所有分支修复完成!"
echo ""
echo "📊 分支状态:"
git branch -a
echo ""
echo "🎯 当前分支: main"
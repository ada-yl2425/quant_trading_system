#!/bin/bash

# 简单修复脚本 - 基于main分支创建各个功能分支

set -e

echo "🛠️  基于main分支创建功能分支..."
echo "=============================================="

# 确保在main分支且是最新
git checkout main
git pull origin main

create_feature_branch() {
    local branch_name=$1
    local files_to_keep=$2
    local commit_msg=$3
    
    echo ""
    echo "创建分支: $branch_name"
    
    # 从main创建分支
    git checkout -b $branch_name
    
    # 删除不需要的文件，只保留指定的文件
    # 首先找出所有文件，然后删除不在保留列表中的文件
    find . -type f -name "*.py" -o -name "*.md" -o -name "*.txt" -o -name ".gitignore" | while read file; do
        file_basename=$(basename "$file")
        keep=false
        for keep_file in $files_to_keep; do
            if [ "$file_basename" = "$keep_file" ]; then
                keep=true
                break
            fi
        done
        
        if [ "$keep" = "false" ] && [ "$file" != "./.gitignore" ]; then
            git rm "$file" 2>/dev/null || true
        fi
    done
    
    # 提交更改
    git add .
    if ! git diff --cached --quiet; then
        git commit -m "$commit_msg"
    fi
    
    # 推送到远程
    git push -u origin $branch_name
    
    # 回到main分支
    git checkout main
    
    echo "✅ $branch_name 创建完成"
}

# 创建各个功能分支
create_feature_branch "base-infrastructure" "config.py requirements.txt" "feat: add base configuration and dependencies"
create_feature_branch "data-loader" "data_loader.py" "feat: implement data loading and cleaning modules"
create_feature_branch "feature-processor" "feature_processor.py" "feat: implement feature engineering and selection modules"
create_feature_branch "signal-builder" "signal_builder.py" "feat: implement online learning model and portfolio management"
create_feature_branch "backtester" "backtester.py" "feat: implement enhanced backtesting engine"
create_feature_branch "main-program" "main.py" "feat: implement main program with complete pipeline"
create_feature_branch "documentation" "README.md" "docs: add comprehensive project documentation"

# 特殊处理dataset-structure分支
echo ""
echo "创建分支: dataset-structure"
git checkout -b dataset-structure

# 删除所有Python和文档文件，只保留目录结构
find . -name "*.py" -delete
find . -name "*.md" -delete
find . -name "*.txt" -delete

# 确保目录结构存在
mkdir -p dataset/raw_data dataset/processed_data output/csv_results output/charts
touch dataset/raw_data/.gitkeep dataset/processed_data/.gitkeep output/csv_results/.gitkeep output/charts/.gitkeep

git add dataset/ output/
git commit -m "feat: add dataset and output directory structure"
git push -u origin dataset-structure

# 回到main分支
git checkout main

echo ""
echo "=============================================="
echo "✅ 所有功能分支创建完成!"
echo ""
echo "📋 创建的分支:"
echo "   - base-infrastructure"
echo "   - data-loader" 
echo "   - feature-processor"
echo "   - signal-builder"
echo "   - backtester"
echo "   - main-program"
echo "   - documentation"
echo "   - dataset-structure"、

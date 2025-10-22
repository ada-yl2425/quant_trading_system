#!/bin/bash

# 步骤1：基础架构
echo "Step 1: Pushing base infrastructure..."
git checkout -b base-infrastructure
git add config.py requirements.txt .gitignore
git commit -m "feat: add base configuration and dependencies"
git push -u origin base-infrastructure

# 步骤2：数据加载模块
echo "Step 2: Pushing data loader module..."
git checkout base-infrastructure
git checkout -b data-loader
git add data_loader.py
git commit -m "feat: implement data loading and cleaning modules"
git push -u origin data-loader

# 步骤3：特征处理模块
echo "Step 3: Pushing feature processor module..."
git checkout data-loader
git checkout -b feature-processor
git add feature_processor.py
git commit -m "feat: implement feature engineering and selection modules"
git push -u origin feature-processor

# 步骤4：信号生成模块
echo "Step 4: Pushing signal builder module..."
git checkout feature-processor
git checkout -b signal-builder
git add signal_builder.py
git commit -m "feat: implement online learning model and portfolio management"
git push -u origin signal-builder

# 步骤5：回测引擎
echo "Step 5: Pushing backtester module..."
git checkout signal-builder
git checkout -b backtester
git add backtester.py
git commit -m "feat: implement enhanced backtesting engine"
git push -u origin backtester

# 步骤6：主程序
echo "Step 6: Pushing main program..."
git checkout backtester
git checkout -b main-program
git add main.py
git commit -m "feat: implement main program with complete pipeline"
git push -u origin main-program

# 步骤7：文档
echo "Step 7: Pushing documentation..."
git checkout main-program
git checkout -b documentation
git add README.md
git commit -m "docs: add comprehensive project documentation"
git push -u origin documentation

# 步骤8：数据集结构
echo "Step 8: Pushing dataset structure..."
git checkout documentation
git checkout -b dataset-structure
mkdir -p dataset/raw_data dataset/processed_data output/csv_results output/charts
touch dataset/raw_data/.gitkeep dataset/processed_data/.gitkeep output/csv_results/.gitkeep output/charts/.gitkeep
git add dataset/ output/
git commit -m "feat: add dataset and output directory structure"
git push -u origin dataset-structure

# 步骤9：创建主分支
echo "Step 9: Creating main branch..."
git checkout -b main
git merge --squash dataset-structure
git commit -m "feat: complete quantitative trading system with all modules"
git push -u origin main

# 步骤10：创建版本标签
echo "Step 10: Creating version tag..."
git tag v1.0.0
git push origin v1.0.0

# 步骤11：创建开发分支
echo "Step 11: Creating develop branch..."
git checkout main
git checkout -b develop
git push -u origin develop

echo "All steps completed successfully!"
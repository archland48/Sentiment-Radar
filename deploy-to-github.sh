#!/bin/bash

# Deploy Sentiment Alpha Radar to GitHub

set -e

echo "🚀 Deploying Sentiment Alpha Radar to GitHub..."
echo ""

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Not a git repository. Please run 'git init' first."
    exit 1
fi

# Check if remote already exists
if git remote get-url origin > /dev/null 2>&1; then
    REMOTE_URL=$(git remote get-url origin)
    echo "📦 Found existing remote: $REMOTE_URL"
    read -p "Do you want to use this remote? (Y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        echo "✅ Using existing remote"
    else
        read -p "Enter new GitHub repository URL: " NEW_REMOTE
        git remote set-url origin "$NEW_REMOTE"
        echo "✅ Updated remote to: $NEW_REMOTE"
    fi
else
    echo "📦 No remote repository configured."
    echo ""
    echo "Please create a GitHub repository first:"
    echo "1. Go to https://github.com/new"
    echo "2. Repository name: sentiment-radar (or your preferred name)"
    echo "3. Choose Public or Private"
    echo "4. DO NOT initialize with README, .gitignore, or license"
    echo "5. Click 'Create repository'"
    echo ""
    read -p "Enter your GitHub repository URL (e.g., https://github.com/username/sentiment-radar.git): " REPO_URL
    
    if [ -z "$REPO_URL" ]; then
        echo "❌ Repository URL is required"
        exit 1
    fi
    
    git remote add origin "$REPO_URL"
    echo "✅ Added remote: $REPO_URL"
fi

# Check if there are uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo "⚠️  You have uncommitted changes."
    read -p "Do you want to commit them now? (Y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        git add -A
        read -p "Enter commit message (or press Enter for default): " COMMIT_MSG
        if [ -z "$COMMIT_MSG" ]; then
            COMMIT_MSG="Update before GitHub deployment"
        fi
        git commit -m "$COMMIT_MSG"
        echo "✅ Changes committed"
    fi
fi

# Push to GitHub
echo ""
echo "📤 Pushing to GitHub..."
echo ""

# Get current branch name
BRANCH=$(git branch --show-current)

echo "Pushing branch: $BRANCH"
git push -u origin "$BRANCH"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Successfully pushed to GitHub!"
    echo ""
    REMOTE_URL=$(git remote get-url origin)
    echo "🌐 Your repository is available at:"
    echo "   $REMOTE_URL"
    echo ""
    echo "To view your repository, visit:"
    if [[ $REMOTE_URL == *"github.com"* ]]; then
        REPO_PATH=$(echo "$REMOTE_URL" | sed -E 's|.*github.com[:/](.+)(\.git)?$|\1|')
        echo "   https://github.com/$REPO_PATH"
    fi
else
    echo "❌ Failed to push to GitHub"
    echo "   Make sure you have:"
    echo "   1. Created the repository on GitHub"
    echo "   2. Proper authentication (SSH key or GitHub CLI)"
    exit 1
fi

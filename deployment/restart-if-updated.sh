#!/usr/bin/env sh

# Log everything and exit if the script fails
set -euxo pipefail

# Set the branch to pull from to develop or the first argument
BRANCH=${1:-develop}

# Change directory to the root of the git repo
cd "$(dirname "$0")/.."

# Pull updates
git fetch origin $BRANCH -q

reslog=$(git log HEAD..origin/$BRANCH --oneline)

# If there is an update to remote
if [[ "${reslog}" != "" ]]; then
    echo have to update at `date`
    # Merge the branch
    git merge origin/$BRANCH
    # Install any new dependencies
    pip3 install --user -r requirements.txt

    cd src
    # Collect any static stuff, in case new static files were added
    python3 manage.py collectstatic --no-input
    # Run migrations, in case new migrations were added
    python3 manage.py migrate
    # Restart the server
    sudo systemctl restart gunicorn
    echo update successful at `date`
fi


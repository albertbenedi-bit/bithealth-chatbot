#!/bin/bash

# Configuration
ORG="bithealth-id"
TEAM_SLUG="data-team-all" # The slug is the URL-friendly name of the team
DRY_RUN=false

# Check for --dry-run flag
if [[ "$1" == "--dry-run" ]]; then
  DRY_RUN=true
  echo "--- DRY RUN MODE --- No changes will be made."
fi

echo "Assigning 'pull' (read-only) permission to team '$TEAM_SLUG' for all repositories in organization '$ORG'..."

# Get all repositories in the organization
# --limit 1000 is used to ensure all repositories are fetched, as default is 30.
# Adjust if your organization has more than 1000 repositories.
# --json name is used to get just the name field in JSON format.
# jq -r '.[].name' extracts the name values as raw strings.
REPOSITORIES=$(gh repo list "$ORG" --limit 1000 --json name --jq '.[].name')

if [ -z "$REPOSITORIES" ]; then
  echo "No repositories found for organization '$ORG' or an error occurred."
  exit 1
fi

# Loop through each repository and add the team with 'pull' permission
for REPO_NAME in $REPOSITORIES; do
  echo "Processing repository: $REPO_NAME"
  
  if [ "$DRY_RUN" = true ]; then
    echo "DRY RUN: Would assign 'pull' permission to '$TEAM_SLUG' for '$REPO_NAME'."
  else
    # GitHub API endpoint for adding/updating team repository permissions
    # PUT /orgs/{org}/teams/{team_slug}/repos/{owner}/{repo}
    gh api \
      --method PUT \
      -H "Accept: application/vnd.github.v3.repository+json" \
      "/orgs/$ORG/teams/$TEAM_SLUG/repos/$ORG/$REPO_NAME" \
      -f permission="pull" --silent

    if [ $? -eq 0 ]; then
      echo "Successfully assigned 'pull' permission to '$TEAM_SLUG' for '$REPO_NAME'."
    else
      echo "Error assigning permission to '$TEAM_SLUG' for '$REPO_NAME'. Please check the output above."
    fi
  fi
  echo "---"
done

echo "Script finished."
#!/usr/bin/env bash
set -euo pipefail

# set origin, destination and list of target modules
ORIG="src/lambda_modules"
DEST="packages/layer"
OUT_ZIP="api_modules_layer.zip"
MODULES=(
    "models"
    "api_logger.py"
)

# make temp dir and store its address
TMP_DIR="$(mktemp -d)"

# set EXIT trap to remove temp dir when we're done
trap 'rm -rf "$TMP_DIR"' EXIT

# make temp/python
mkdir "$TMP_DIR/python"
# loop over the modules, copying each to temp/python
for MODULE in "${MODULES[@]}"; do
    cp -r "$ORIG/$MODULE" "$TMP_DIR/python"
done

# delete pycache files
find "$TMP_DIR" -type d -name "__pycache__" -prune -exec rm -rf {} +

# make sure the destination exists
mkdir -p "$DEST"
# if the zip already exists, delete it to avoid stale files
rm -f "$DEST/$OUT_ZIP"
# get the absolute path of the destination
DEST_ABS="$(cd "$DEST" && pwd)"

# cd into the temp dir so that paths in the zip start with python/
(cd "$TMP_DIR" && zip -r "$DEST_ABS/$OUT_ZIP" "python")

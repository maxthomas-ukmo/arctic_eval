# Copy the plots, index, and optionally the data to /data, then symlink to public_html and open with firefox

recipe_name=$1
recipe_name_for_webpage=$2

if [ -z "$1" ]; then
    echo "Usage: ./archive_recipe.sh <recipe_name> <recipe_name_for_webpage>"
    echo "For example: ./archive_recipe.sh recipe_arctic_ocean_20241022_134333 recipe_arctic_ocean-First_working_HadGEM-MM"
    echo "Exiting without doing anything as first argument must be provided."
    exit 1
fi

if [ -z "$2" ]; then
    echo "No alternate name provided for the webpage, using the recipe name."
    recipe_name_for_webpage=$recipe_name
fi
echo "Archiving recipe $recipe_name"

ARCHIVE_DIR=~/public_html/esmvaltool/$recipe_name_for_webpage
echo "ARCHIVE_DIR: " $ARCHIVE_DIR

RAW_DIR=/data/users/max.thomas/esmvaltool/esmvaltool_output/$1
echo "RAW_DIR: " $RAW_DIR

echo "Linking dir"

# Symlink to public_html
ln -s $RAW_DIR/. $ARCHIVE_DIR

cd $ARCHIVE_DIR
ls -l
firefox index.html

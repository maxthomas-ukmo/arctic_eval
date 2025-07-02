# Copy the plots, index, and optionally the data to /data, then symlink to public_html and open with firefox

recipe_name=$1
archive_data=$2
recipe_name_for_webpage=$3

if [ -z "$1" ]; then
    echo "Usage: ./archive_recipe.sh <recipe_name> <archive_data> <recipe_name_for_webpage>"
    echo "For example: ./archive_recipe.sh recipe_arctic_ocean_20241022_134333 true recipe_arctic_ocean-First_working_HadGEM-MM"
    echo "Exiting without doing anything as first argument must be provided."
    exit 1
fi

if [ -z "$3" ]; then
    echo "No alternate name provided for the webpage, using the recipe name."
    recipe_name_for_webpage=$recipe_name
fi
echo "Archiving recipe $recipe_name"

ARCHIVE_DIR=/data/users/max.thomas/esmvaltool/esmvaltool_output/$recipe_name_for_webpage
echo "ARCHIVE_DIR: " $ARCHIVE_DIR

RAW_DIR=/data/users/max.thomas/esmvaltool/esmvaltool_output/$1
echo "RAW_DIR: " $RAW_DIR

# check if $2 is true or false
if [ "$2" == "true" ]; then
    echo "Archiving data"
    mkdir -p $ARCHIVE_DIR
    cp -r $RAW_DIR $ARCHIVE_DIR
else
    echo "Just archiving plots and webpage"
    mkdir -p $ARCHIVE_DIR
    cp -r $RAW_DIR/{plots/,index.html} $ARCHIVE_DIR
fi

# Symlink to public_html
cd /home/users/max.thomas/public_html/esmvaltool/
cp -r $ARCHIVE_DIR .

ls -l
firefox $recipe_name_for_webpage/index.html

echo "creating $2 (second command line arg)"
echo "from $1 (.lock file path, downloaded as per https://www-avd/sci/software_stack/conda_how_to_extend.html)"
conda create --name ${2} --file ${1}

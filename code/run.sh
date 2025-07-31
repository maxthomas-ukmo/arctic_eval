# Default values
mem="128G"
recipe=$1

# If log file not specified, default to <recipe>.log
if [ -z "$log" ]; then
  log="${recipe}.log"
fi

echo "Running recipe: $recipe"
echo "Memory: $mem"
echo "Log file: $log-$mem"

# Run ESMValTool with srun, using specified memory and time limit
# Output is piped to both terminal and log file
srun --mem=$mem --time=120 bash run_esmvaltool.sh $recipe | tee $log
for c in config/*
do
	for f in $c/*
	do
 	# echo "Processing $f" # always double quote "$f" filename
 	# echo "I would copy $f/18x24.json to $f/b2.json"
	cp --verbose -n $f/24x36.json $f/b1.json
	# do something on $f
	done
done

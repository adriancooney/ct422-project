#!/bin/sh

DATE=`date +%d%m%Y-%H%M`
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd "$DIR/../data/dumps/"
echo "Dumping database exam_papers.."
pg_dump exam_papers -C -O -c -x > "exam_papers-$DATE.sql"
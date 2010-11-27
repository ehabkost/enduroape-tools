while read f;do
	sox -t wav "$f"
done < <(find sounds -name '*.wav')

<form enctype="multipart/form-data" action="index.php" method="POST">
<input type="hidden" name="MAX_FILE_SIZE" value="100000" />
Choose a file to upload: <input name="uploadedfile" type="file" /><br />

<input type="text" name="passos" value="<?if(empty($passos)) echo "1.6"; else echo $passos;?>" /> Tamanho do passo
<input type="submit" value="Calcular" />
</form>

<?
    
    date_default_timezone_set('UTC'); 

    if(empty($passos))
        die();
    $delete=0;
    $pag=0;
    $referencia=1;
    $tempoanterior=0;
    $file = fopen($_FILES['uploadedfile']['tmp_name'], "r") or exit("Unable to open file!");
    //Output a line of the file until the end is reached
    echo "<table border=\"1\">";
    while(!feof($file))
    {
      $line=trim(fgets($file));

      if($line=="-")
      {
	echo "<br/>Pagina <font color=Blue><b>". $pag++ ."</b></font> <hr/><br><br>";
	echo "</table>";
    	echo "<table border=\"1\">";
	continue;
      }
      if($line=="NEUTRO")
      {
        $tempo=fgets($file);
        $tempo_trim=trim($tempo);
	echo "<tr><td>$referencia</td><td><br/>&nbsp;&nbsp;&nbsp; <font color=red><b>********** NEUTRO -> partir as $tempo_trim *************</b></font><br/><br/></td></tr>";
	$referencia++;
        $tempoanterior=$tempo;
        continue;
      }
      if(is_numeric($line))
      {
          $steps=round($line/$passos);
          if($steps <= 10)
          {
              $tempo=fgets($file);
	      echo "<tr><td>$referencia</td><td>$line metros -> $steps passos -> chegada as $tempo<br/></td></tr>";
	      $referencia++;
              // joga fora o lixo
              fgets($file);
              $tempoanterior=$tempo;
              continue;
          }

          if($steps > 10 && $steps <= 30)
          {
              $tempo=fgets($file);
	      echo "<tr><td>$referencia</td><td>$line metros -> $steps passos -> chegada as $tempo";
	      $referencia++;
              // joga fora no lixo
              fgets($file);

              echo "<br/>&nbsp;&nbsp;&nbsp;Parciais:<br/>";
              // divide por 2
              $hours_diff = (strtotime($tempo)-strtotime($tempoanterior))/2;
              $half = strtotime($tempoanterior) + $hours_diff;
              echo "&nbsp;&nbsp;&nbsp;".date('H:i:s', $half)." -> ". round($steps/2) ." passos -> metragem ".$passos*round($steps/2) ."<br/><br/></td></tr>"; 
              $tempoanterior=$tempo;
              continue;
          }
          if($steps > 30 && $steps <= 80)
          {
              $tempo=fgets($file);
	      echo "<tr><td>$referencia</td><td>$line metros -> $steps passos -> chegada as $tempo";
	      $referencia++;
              // joga fora no lixo
              fgets($file);

              echo "<br/>&nbsp;&nbsp;&nbsp;Parciais:<br/>";
              // divide por 4
              $hours_diff = (strtotime($tempo)-strtotime($tempoanterior))*(1/4);
              $half = strtotime($tempoanterior) + $hours_diff;
              echo "&nbsp;&nbsp;&nbsp;".date('H:i:s', $half)." -> ". round($steps*(1/4)) ." passos -> metragem ".$passos*round($steps*(1/4)) ."<br/>";

              $hours_diff = (strtotime($tempo)-strtotime($tempoanterior))*(2/4);
              $half = strtotime($tempoanterior) + $hours_diff;
              echo "&nbsp;&nbsp;&nbsp;".date('H:i:s', $half)." -> ". round($steps*(2/4)) ." passos -> metragem ".$passos*round($steps*(2/4)) ."<br/>";

              $hours_diff = (strtotime($tempo)-strtotime($tempoanterior))*(3/4);
              $half = strtotime($tempoanterior) + $hours_diff;
              echo "&nbsp;&nbsp;&nbsp;".date('H:i:s', $half)." -> ". round($steps*(3/4)) ." passos -> metragem ".$passos*round($steps*(3/4)) ."<br/>";

              $hours_diff = (strtotime($tempo)-strtotime($tempoanterior))*(4/4);
              $half = strtotime($tempoanterior) + $hours_diff;
              echo "&nbsp;&nbsp;&nbsp;".date('H:i:s', $half)." -> ". round($steps*(4/4)) ." passos -> metragem ".$passos*round($steps*(4/4)) ."<br/><br/></td></tr>";


              $tempoanterior=$tempo;
              continue;
          }
          if($steps > 80 && $steps <= 160)
          {
              $tempo=fgets($file);
	      echo "<tr><td>$referencia</td><td>$line metros -> $steps passos -> chegada as $tempo";
	      $referencia++;
              // joga fora no lixo
              fgets($file);

              echo "<br/>&nbsp;&nbsp;&nbsp;Parciais:<br/>";
              // divide por 8
              $hours_diff = (strtotime($tempo)-strtotime($tempoanterior))*(1/8);
              $half = strtotime($tempoanterior) + $hours_diff;
              echo "&nbsp;&nbsp;&nbsp;".date('H:i:s', $half)." -> ". round($steps*(1/8)) ." passos -> metragem ".$passos*round($steps*(1/8)) ."<br/>";

              $hours_diff = (strtotime($tempo)-strtotime($tempoanterior))*(2/8);
              $half = strtotime($tempoanterior) + $hours_diff;
              echo "&nbsp;&nbsp;&nbsp;".date('H:i:s', $half)." -> ". round($steps*(2/8)) ." passos -> metragem ".$passos*round($steps*(2/8)) ."<br/>";

              $hours_diff = (strtotime($tempo)-strtotime($tempoanterior))*(3/8);
              $half = strtotime($tempoanterior) + $hours_diff;
              echo "&nbsp;&nbsp;&nbsp;".date('H:i:s', $half)." -> ". round($steps*(3/8)) ." passos -> metragem ".$passos*round($steps*(3/8)) ."<br/>";

              $hours_diff = (strtotime($tempo)-strtotime($tempoanterior))*(4/8);
              $half = strtotime($tempoanterior) + $hours_diff;
              echo "&nbsp;&nbsp;&nbsp;".date('H:i:s', $half)." -> ". round($steps*(4/8)) ." passos -> metragem ".$passos*round($steps*(4/8)) ."<br/>";

              $hours_diff = (strtotime($tempo)-strtotime($tempoanterior))*(5/8);
              $half = strtotime($tempoanterior) + $hours_diff;
              echo "&nbsp;&nbsp;&nbsp;".date('H:i:s', $half)." -> ". round($steps*(5/8)) ." passos -> metragem ".$passos*round($steps*(5/8)) ."<br/>";

              $hours_diff = (strtotime($tempo)-strtotime($tempoanterior))*(6/8);
              $half = strtotime($tempoanterior) + $hours_diff;
              echo "&nbsp;&nbsp;&nbsp;".date('H:i:s', $half)." -> ". round($steps*(6/8)) ." passos -> metragem ".$passos*round($steps*(6/8)) ."<br/>";

              $hours_diff = (strtotime($tempo)-strtotime($tempoanterior))*(7/8);
              $half = strtotime($tempoanterior) + $hours_diff;
              echo "&nbsp;&nbsp;&nbsp;".date('H:i:s', $half)." -> ". round($steps*(7/8)) ." passos -> metragem ".$passos*round($steps*(7/8)) ."<br/>";

              $hours_diff = (strtotime($tempo)-strtotime($tempoanterior))*(8/8);
              $half = strtotime($tempoanterior) + $hours_diff;
              echo "&nbsp;&nbsp;&nbsp;".date('H:i:s', $half)." -> ". round($steps*(8/8)) ." passos -> metragem ".$passos*round($steps*(8/8)) ."<br/><br/></td></tr>";

              $tempoanterior=$tempo;
              continue;
          }
          if($steps > 160)
          {
              $tempo=fgets($file);
	      echo "<tr><td>$referencia</td><td>$line metros -> $steps passos -> chegada as $tempo";
	      $referencia++;
              // joga fora no lixo
              fgets($file);

              echo "<br/>&nbsp;&nbsp;&nbsp;Parciais:<br/>";
              // divide por 16
              $hours_diff = (strtotime($tempo)-strtotime($tempoanterior))*(1/16);
              $half = strtotime($tempoanterior) + $hours_diff;
              echo "&nbsp;&nbsp;&nbsp;".date('H:i:s', $half)." -> ". round($steps*(1/16)) ." passos -> metragem ".$passos*round($steps*(1/16)) ."<br/>";

              $hours_diff = (strtotime($tempo)-strtotime($tempoanterior))*(2/16);
              $half = strtotime($tempoanterior) + $hours_diff;
              echo "&nbsp;&nbsp;&nbsp;".date('H:i:s', $half)." -> ". round($steps*(2/16)) ." passos -> metragem ".$passos*round($steps*(2/16)) ."<br/>";

              $hours_diff = (strtotime($tempo)-strtotime($tempoanterior))*(3/16);
              $half = strtotime($tempoanterior) + $hours_diff;
              echo "&nbsp;&nbsp;&nbsp;".date('H:i:s', $half)." -> ". round($steps*(3/16)) ." passos -> metragem ".$passos*round($steps*(3/16)) ."<br/>";

              $hours_diff = (strtotime($tempo)-strtotime($tempoanterior))*(4/16);
              $half = strtotime($tempoanterior) + $hours_diff;
              echo "&nbsp;&nbsp;&nbsp;".date('H:i:s', $half)." -> ". round($steps*(4/16)) ." passos -> metragem ".$passos*round($steps*(4/16)) ."<br/>";

              $hours_diff = (strtotime($tempo)-strtotime($tempoanterior))*(5/16);
              $half = strtotime($tempoanterior) + $hours_diff;
              echo "&nbsp;&nbsp;&nbsp;".date('H:i:s', $half)." -> ". round($steps*(5/16)) ." passos -> metragem ".$passos*round($steps*(5/16)) ."<br/>";

              $hours_diff = (strtotime($tempo)-strtotime($tempoanterior))*(6/16);
              $half = strtotime($tempoanterior) + $hours_diff;
              echo "&nbsp;&nbsp;&nbsp;".date('H:i:s', $half)." -> ". round($steps*(6/16)) ." passos -> metragem ".$passos*round($steps*(6/16)) ."<br/>";

              $hours_diff = (strtotime($tempo)-strtotime($tempoanterior))*(7/16);
              $half = strtotime($tempoanterior) + $hours_diff;
              echo "&nbsp;&nbsp;&nbsp;".date('H:i:s', $half)." -> ". round($steps*(7/16)) ." passos -> metragem ".$passos*round($steps*(7/16)) ."<br/>";

              $hours_diff = (strtotime($tempo)-strtotime($tempoanterior))*(8/16);
              $half = strtotime($tempoanterior) + $hours_diff;
              echo "&nbsp;&nbsp;&nbsp;".date('H:i:s', $half)." -> ". round($steps*(8/16)) ." passos -> metragem ".$passos*round($steps*(8/16)) ."<br/>";
              
              $hours_diff = (strtotime($tempo)-strtotime($tempoanterior))*(9/16);
              $half = strtotime($tempoanterior) + $hours_diff;
              echo "&nbsp;&nbsp;&nbsp;".date('H:i:s', $half)." -> ". round($steps*(9/16)) ." passos -> metragem ".$passos*round($steps*(9/16)) ."<br/>";

              $hours_diff = (strtotime($tempo)-strtotime($tempoanterior))*(10/16);
              $half = strtotime($tempoanterior) + $hours_diff;
              echo "&nbsp;&nbsp;&nbsp;".date('H:i:s', $half)." -> ". round($steps*(10/16)) ." passos -> metragem ".$passos*round($steps*(10/16)) ."<br/>";

              $hours_diff = (strtotime($tempo)-strtotime($tempoanterior))*(11/16);
              $half = strtotime($tempoanterior) + $hours_diff;
              echo "&nbsp;&nbsp;&nbsp;".date('H:i:s', $half)." -> ". round($steps*(11/16)) ." passos -> metragem ".$passos*round($steps*(11/16)) ."<br/>";

              $hours_diff = (strtotime($tempo)-strtotime($tempoanterior))*(12/16);
              $half = strtotime($tempoanterior) + $hours_diff;
              echo "&nbsp;&nbsp;&nbsp;".date('H:i:s', $half)." -> ". round($steps*(12/16)) ." passos -> metragem ".$passos*round($steps*(12/16)) ."<br/>";

              $hours_diff = (strtotime($tempo)-strtotime($tempoanterior))*(13/16);
              $half = strtotime($tempoanterior) + $hours_diff;
              echo "&nbsp;&nbsp;&nbsp;".date('H:i:s', $half)." -> ". round($steps*(13/16)) ." passos -> metragem ".$passos*round($steps*(13/16)) ."<br/>";

              $hours_diff = (strtotime($tempo)-strtotime($tempoanterior))*(14/16);
              $half = strtotime($tempoanterior) + $hours_diff;
              echo "&nbsp;&nbsp;&nbsp;".date('H:i:s', $half)." -> ". round($steps*(14/16)) ." passos -> metragem ".$passos*round($steps*(14/16)) ."<br/>";

              $hours_diff = (strtotime($tempo)-strtotime($tempoanterior))*(15/16);
              $half = strtotime($tempoanterior) + $hours_diff;
              echo "&nbsp;&nbsp;&nbsp;".date('H:i:s', $half)." -> ". round($steps*(15/16)) ." passos -> metragem ".$passos*round($steps*(15/16)) ."<br/>";

              $hours_diff = (strtotime($tempo)-strtotime($tempoanterior))*(16/16);
              $half = strtotime($tempoanterior) + $hours_diff;
              echo "&nbsp;&nbsp;&nbsp;".date('H:i:s', $half)." -> ". round($steps*(16/16)) ." passos -> metragem ".$passos*round($steps*(16/16)) ."<br/><br/></td></tr>";

              $tempoanterior=$tempo;
              continue;
          }
      }
    }
    fclose($file);
?> 


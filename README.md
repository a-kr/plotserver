plotserver
==========
Примитивная штука, собирающая числовые значения и строящая графики изменения этих значений во времени.
Поддерживает произвольное число независимых графиков.

Данные для графиков хранятся на диске в текстовых файлах.

Не проверялась на сколь-либо серьезных нагрузках. Обновление данных и запрос графиков раз в 5 секунд выдержит, на большее расчитывать не стоит.

Зависимости
-----------
 * python 2.7
 * flask
 * gnuplot

Использование
-------------
 
 1. Копируем example_plotserver_config.py в plotserver_config.py
 2. Меняем в plotserver_config.py значение SECRET_KEY
 3. Запускаем: `python plotserver.py`
 4. Придумываем имя для графика. Например "my_mega_plot"
 5. Выясняем пароли на чтение и запись:
    
        ~/plotserver$ python plotserver.py get-trust-key my_mega_plot
        Write key: 7a351d23
        Read key:  40a0a49d
    
 6. Используем следующий URL для добавления значения на график:
        
        http://localhost:5101/my_mega_plot/push?v=123trustkey=7a351d23
 
 7. Используем следующие URL для получения графика в виде PNG-картинки:
        
        http://localhost:5101/my_mega_plot/graph.png?trustkey=40a0a49d
        http://localhost:5101/my_mega_plot/graph-640x480.png?trustkey=40a0a49d

 8. Аналогичным образом создаем и заполняем сколько угодно других графиков.

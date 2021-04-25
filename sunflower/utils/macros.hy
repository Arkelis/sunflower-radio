;; Helper macro for defining channels with Hy

(defmacro slot [start end station]
  `(, ~start ~end ~station))

(defmacro days [days #* slots]
  `(, (tuple ~days) ~slots))

(defmacro channel [id name handlers #* days]
  `{"id" (str '~id)
    "name" ~name
    "handlers" ~handlers
    "timetable" (dict ~days)})

(defmacro def-channels [#* channels]
  `(, "channels" (dfor c ~channels [(get c "id") c])))

(defmacro station [id name]
  `{"id" (str '~id) "name" ~name})

(defmacro def-stations [#* stations]
  `(, "stations" (dfor s ~stations [(get s "id") s])))

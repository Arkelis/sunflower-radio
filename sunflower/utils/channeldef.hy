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
  `(setv channels-definitions
    (dfor c ~channels [(get c "id") c])))

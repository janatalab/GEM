module GDFInfo
using GEMDataReader
import JSON

export dumpinfo

dumpinfo(ifile::String) = dumpinfo(GEMDataFile(ifile))

function dumpinfo(gd::GEMDataFile)
    p = Vector{Int}(gd.nrun)
    open(gd.path, "r") do io
       for k in 1:gd.nrun
           # seek to begining of run header
           seek(io, gd.idx_map[k])

           # size of run header in bytes
           sz = read(io, UInt64)

           # read the header
           hdr = JSON.parse(String(read(io, UInt8, sz)))

           if k < gd.nrun
               # number of bytes in data block is the position of the start of
               # the next run header minus the current position (start of data
               # block)
               p[k] = gd.idx_map[k+1] - position(io)

           else
               # size of data block is number of bytes in  file minus the
               # current position (start of data block)
               tmp2 = position(io)
               tmp = seekend(io)
               p[k] = position(io) - tmp2
           end
       end
   end
   # println("""Data size: $(sum(p)/17)
   # Expected size: $(gd.nrun*gd.nwin)
   # """)
   return p
end

end

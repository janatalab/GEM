module GEMDataReader

import JSON
using FileOps
export convert_file, convert_files, GEMDataFile, read_run

const MAX_TAPPERS = 0x04
# ---------------------------------------------------------------------------- #
struct GEMDataFile
    path::String
    hdr::Dict
    idx_map::Vector{UInt64}
    nrun::Int
    nwin::Int
end
# ---------------------------------------------------------------------------- #
struct GEMPacket
    dtp::UInt8
    window::UInt16
    click_time::UInt32
    async::Vector{Int16}
    adjust::Int16
end
# ---------------------------------------------------------------------------- #
function GEMDataFile(filepath::String)
    open(filepath, "r") do io
        hdr_length = read(io, UInt64)
        println("Header length: ", hdr_length)

        # hdr = JSON.parse(String(read(io, UInt8, hdr_length)))
        hdr = JSON.parse(String(read(io, hdr_length)))
        println("Header: ", hdr)

        nrun = length(hdr["metronome_alpha"]) * Int64(hdr["repeats"])
        println("#runs: ", nrun)

        # idx_map = read(io, UInt64, nrun)
        idx_map = reinterpret(UInt64, read(io, nrun*sizeof(UInt64)))
        println("Run index map: ", idx_map)

        return GEMDataFile(filepath, hdr, idx_map, nrun, Int(hdr["windows"]))
    end
end
# ---------------------------------------------------------------------------- #
function swapext(file::String, ext::String)
    ext = ext[1] == "." ? ext : "." * ext
    return splitext(file)[1] * ext
end
# ---------------------------------------------------------------------------- #
"""
    ofiles = convert_files(dir::String, force::Bool=false, depth::Integer=1)

# In:
- `dir::String`: the path to a base directory to search within
- `force::Bool`: true to force reconversion of gdf files where the resulting csv file already exists
- `depth::Integer`: the depth of sub-directories to search

# Out:
- `ofiles::Vector{String}`: resulting csv files paths (successful conversions only)

# Examples:

```julia
ofiles = convert_files("../Data/")
```
"""
function convert_files(dir::String, force::Bool=false, depth::Integer=1)
    dirs = find_directories(dir, r"\d{8}")
    for k in eachindex(dirs)
        for j in 1:depth-1
            # only folders named as yyyymmdd
            append!(dirs, find_directories(dirs[j], r"\d{8}"))
        end
    end

    files = Vector{String}()
    for dir in dirs
        append!(files, find_files(dir, r"\.gdf$"))
    end

    ofiles = Vector{String}()

    for k in eachindex(files)
        ofile = swapext(files[k], "csv")
        if !isfile(ofile) || force
            try
                convert_file(files[k], ofile)
                push!(ofiles, ofile)
            catch err
                warn("Failed to convert file: \"$(files[k])\" - $(err)")
            end
        end
    end
    return ofiles
end
# ---------------------------------------------------------------------------- #
function convert_file(ifile::String, ofile::String)

    df = GEMDataFile(ifile)
    hdrs = Vector{Dict}()

    open(ofile, "w") do io
        labels = join(["\"async_$(x)\"" for x in 1:MAX_TAPPERS], ", ")
        write(io,
            """
            \"run\", \"alpha\", \"window\", \"click_time\", $(labels), \"next_adjust\"
            """
        )
        for k = 1:df.nrun
            hdr, data = read_run(df, k)
            if isempty(data)
                break
            end
            push!(hdrs, hdr)
            write_run(io, hdr, data, k)
        end

        # add run headers to the file header dict for output
        df.hdr["run_headers"] = hdrs
    end

    open(swapext(ofile, "json"), "w") do io
        write(io, JSON.json(df.hdr))
    end

    return nothing
end
# ---------------------------------------------------------------------------- #
# Columns: run #, alpha, window #, scheduled click, async 1-4, next_adjust
function write_run(io::IOStream, hdr::Dict, data::Vector{GEMPacket},
    run::Integer)
    for k in eachindex(data)
        write(io, "$(run), $(hdr["alpha"]), $(k), " * tostring(data[k]) * "\n")
    end
end
# ---------------------------------------------------------------------------- #
function tostring(x::GEMPacket)
    return "$(x.click_time), " * join(x.async, ", ") * ", $(x.adjust)"
end
# ---------------------------------------------------------------------------- #
function read_run(file::GEMDataFile, k::Integer=1)
    hdr, offset = read_run_header(file, k)
    if offset > 0
        data = Vector{GEMPacket}(file.nwin)
        open(file.path, "r") do io
            seek(io, offset)

            for k = 1:file.nwin
                data[k] = read_packet(io)
            end
            return hdr, data
        end
    else
        return hdr, Vector{GEMPacket}()
    end
end
# ---------------------------------------------------------------------------- #
"""
returns the run header and the position of the start of the data block for that
run
"""
function read_run_header(file::GEMDataFile, k::Integer=1)
    @assert(k <= file.nrun, "Invalid run number!")

    offset = file.idx_map[k]
    println("Reading header for run ", k, " at offset ", offset)

    if offset > 0
        open(file.path, "r") do io
            seek(io, offset)
            hdr_length = read(io, UInt64)
            println("Header length: ", hdr_length)
            #hdr = JSON.parse(String(read(io, UInt8, hdr_length)))

            hdr = JSON.parse(String(read(io, hdr_length)))
            return hdr, position(io)
        end
    else
        return Dict(), -1
    end

end
# ---------------------------------------------------------------------------- #
function read_packet(io::IOStream)
    return GEMPacket(
        read(io, UInt8),            #data-transfer-protocol id
        read(io, UInt16),           #window number
        read(io, UInt32),           #click_time
        read(io, Int16, MAX_TAPPERS),#asynchronies
        read(io, Int16)             #next adjustment factor
    )
end
# ---------------------------------------------------------------------------- #
end # end module

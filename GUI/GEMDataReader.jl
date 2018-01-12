module GEMDataReader

import JSON

export convert_file, GEMDataFile, read_run

const MAX_SLAVES = 0x04
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
        hdr = JSON.parse(String(read(io, UInt8, hdr_length)))

        nrun = length(hdr["metronome_alpha"]) * Int64(hdr["repeats"])
        idx_map = read(io, UInt64, nrun)

        return GEMDataFile(filepath, hdr, idx_map, nrun, Int(hdr["windows"]))
    end
end
# ---------------------------------------------------------------------------- #
function convert_file(ifile::String, ofile::String)

    df = GEMDataFile(ifile)

    open(ofile, "w") do io
        labels = join(["\"async_$(x)\"" for x in 1:MAX_SLAVES], ", ")
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
            write_run(io, hdr, data, k)
        end
    end

    jfile = splitext(ofile)[1] * ".json"
    open(jfile, "w") do io
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

    if offset > 0
        open(file.path, "r") do io
            seek(io, offset)
            hdr_length = read(io, UInt64)
            return JSON.parse(String(read(io, UInt8, hdr_length))), position(io)
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
        read(io, Int16, MAX_SLAVES),#asynchronies
        read(io, Int16)             #next adjustment factor
    )
end
# ---------------------------------------------------------------------------- #
end # end module

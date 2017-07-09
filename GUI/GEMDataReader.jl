module GEMDataReader

import JSON

const MAX_SLAVES = 0x04

struct GEMDataFile
    path::String
    hdr::Dict
    idx_map::Vector{UInt64}
    nrun::Int
end

struct GEMPacket
    dtp::UInt8
    window::UInt16
    click_time::UInt32
    async::Vector{Int16}
    adjust::Int16
end

function GEMDataFile(filepath::String)
    open(filepath, "r") do io
        hdr_length = read(io, UInt64)
        hdr = JSON.parse(String(read(io, UInt8, hdr_length)))

        nrun = length(hdr["metronome_alpha"]) * Int64(hdr["repeats"])
        idx_map = read(io, UInt64, nrun)

        seekend(io)
        len = position(io)

        return GEMDataFile(filepath, hdr, idx_map, nrun)
    end
end

function convert_file(ifile::String, ofile::String)

    df = GEMDataFile(ifile)

    open(ofile, "w") do io
        for k = 1:df.nrun
            hdr, data = read_run(df, k)
            # TODO: write the run to the text ofile (columns etc.)
        end
    end
end

function read_run(file::GEMDataFile, k::Integer=1)
    hdr, offset = read_run_header(file, k)
    nwin = Int(hdr["windows"])
    data = Vector{GEMPacket}(nwin)
    open(file.path, "r") do io
        seek(io, offset)

        for k = 1:nwin
            data[k] = read_packet(io)
        end
        return hdr, data
    end
end

"""
returns the run header and the position of the start of the data block for that
run
"""
function read_run_header(file::GEMDataFile, k::Integer=1)
    @assert(k > file.nrun, "Invalid run number!")

    offset = file.idx_map[k]

    open(file.path, "r") do io
        seek(io, offset)
        hdr_length = read(io, UInt64)
        return JSON.parse(String(read(io, UInt8, hdr_length))), position(io)
    end
end

function read_packet(io::IOStream)
    return GEMPacket(
        read(io, UInt8),            #data-transfer-protocol id
        read(io, UInt16),           #window number
        read(io, UInt32),           #click_time
        read(io, Int16, MAX_SLAVES),#asynchronies
        read(io, Int16)             #next adjustment factor
    )
end

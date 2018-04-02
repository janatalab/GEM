module FileOps

export find_files, find_directories, read_float_file

# =========================================================================== #
find_files(dir::AbstractString, re=r".*") = return do_match(dir, re, isfile)
# --------------------------------------------------------------------------- #
find_directories(dir::AbstractString, re=r".*") = return do_match(dir, re, isdir)
# --------------------------------------------------------------------------- #
function read_float_file(ifile::AbstractString)
    x = readdlm(ifile, Float64)
    if prod(size(x)) == maximum(size(x))
        x = vec(x)
    end
    return x
end
# =========================================================================== #
function do_match(dir::AbstractString, re::Regex, f::Function)
    if !isdir(dir)
        error("Input is not a vaild directory path")
    end
    files = [joinpath(dir, x) for x in readdir(dir)]
    return filter(x->ismatch(re, x) && f(x), files)
end
# =========================================================================== #
end # END MODULE
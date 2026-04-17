local f_time = Field.new("frame.time_epoch")

local last_time = 0
local packet_count = 0
local total_delta = 0
local max_delta = 0
local min_delta = 999999

local file = io.open("jitter_output.csv", "w")
file:write("packet_number,delta_ms\n")

local tap = Listener.new("frame", "pn_io")

function tap.packet(pinfo, tvb)
    local current_time_field = f_time()
    if not current_time_field then return end

    local current_time = tonumber(tostring(current_time_field))

    if last_time > 0 then
        local delta_t = current_time - last_time
        local delta_ms = delta_t * 1000

        total_delta = total_delta + delta_ms
        packet_count = packet_count + 1

        if delta_ms > max_delta then max_delta = delta_ms end
        if delta_ms < min_delta then min_delta = delta_ms end

        if delta_ms < 0.001 then
            print("Frame Wireshark com delta < 0.001 " .. pinfo.number)
        end
        
        file:write(packet_count .. "," .. delta_ms .. "\n")
    end

    last_time = current_time
end

function tap.draw()
    if packet_count > 0 then
        local avg_delta = total_delta / packet_count
        print("\n==================================================")
        print(" ANALISE TEMPORAL DOS PACOTES PROFINET ")
        print("==================================================")
        print(string.format(" Pacotes analizados : %d", packet_count))
        print(string.format(" Delta mínimo       : %.4f ms", min_delta))
        print(string.format(" Delta máximo       : %.4f ms", max_delta))
        print(string.format(" Delta médio        : %.4f ms", avg_delta))
        print("==================================================\n")
    else
        print("No PROFINET packets found.")
    end
    
    file:close()
end

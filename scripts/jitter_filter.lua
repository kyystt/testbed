local f_time = Field.new("frame.time_epoch")
local f_eth_src = Field.new("eth.src")
local f_iface = Field.new("frame.interface_id")

-- Global trackers
local last_time_global = 0
local packet_count = 0
local total_delta_global = 0
local global_valid_deltas = 0

-- Table to hold tracking data per Source MAC
-- Structure: src_stats[mac] = { last_time, count, total_delta, max_delta, min_delta }
local src_stats = {}

-- Open CSV and write headers
local file = io.open("jitter_output_filtered.csv", "w")
file:write("packet_number,interface_id,src_mac,global_delta_ms,source_delta_ms\n")

local tap = Listener.new("frame", "pn_io")

function tap.packet(pinfo, tvb)
    local current_time_field = f_time()
    local src_mac_field = f_eth_src()
    local iface_field = f_iface()
    
    if not current_time_field or not src_mac_field then return end

    local current_time = tonumber(tostring(current_time_field))
    local src_mac = tostring(src_mac_field)
    local iface_id = iface_field and tostring(iface_field) or "unknown"

    packet_count = packet_count + 1

    -- Initialize tracking for this specific MAC address if seen for the first time
    if not src_stats[src_mac] then
        src_stats[src_mac] = {
            last_time = 0,
            count = 0,
            total_delta = 0,
            max_delta = 0,
            min_delta = 999999
        }
    end

    local stats = src_stats[src_mac]
    local global_delta_ms = 0
    local source_delta_ms = 0

    -- Calculate Global Delta (Time since the absolute previous packet)
    if last_time_global > 0 then
        global_delta_ms = (current_time - last_time_global) * 1000
        total_delta_global = total_delta_global + global_delta_ms
        global_valid_deltas = global_valid_deltas + 1
        
        if global_delta_ms < 0.001 then
            print("Buffer Anomaly (Global) at Frame: " .. pinfo.number .. " | MAC: " .. src_mac)
        end
    end

    -- Calculate Source-Specific Delta (Filter 2: Time since this specific MAC last sent a packet)
    if stats.last_time > 0 then
        source_delta_ms = (current_time - stats.last_time) * 1000
        
        stats.total_delta = stats.total_delta + source_delta_ms
        stats.count = stats.count + 1
        
        if source_delta_ms > stats.max_delta then stats.max_delta = source_delta_ms end
        if source_delta_ms < stats.min_delta then stats.min_delta = source_delta_ms end
    end

    -- Write all data points to CSV
    file:write(string.format("%d,%s,%s,%.6f,%.6f\n", packet_count, iface_id, src_mac, global_delta_ms, source_delta_ms))

    -- Update last seen timestamps
    last_time_global = current_time
    stats.last_time = current_time
end

function tap.draw()
    if packet_count > 0 then
        print("\n=========================================================")
        print(" PROFINET TEMPORAL PACKET ANALYSIS (MULTI-SOURCE) ")
        print("=========================================================")
        print(string.format(" Total Packets Analyzed : %d", packet_count))
        
        if global_valid_deltas > 0 then
            local avg_global = total_delta_global / global_valid_deltas
            print(string.format(" Overall Average Delta  : %.4f ms", avg_global))
        end
        
        print("\n--- STATISTICS PER SOURCE MAC (FILTER 2) ---")
        for mac, stats in pairs(src_stats) do
            if stats.count > 0 then
                local avg_src = stats.total_delta / stats.count
                print(string.format("MAC: %s", mac))
                print(string.format("  Packets tracked : %d", stats.count))
                print(string.format("  Minimum Delta   : %.4f ms", stats.min_delta))
                print(string.format("  Maximum Delta   : %.4f ms", stats.max_delta))
                print(string.format("  Average Delta   : %.4f ms", avg_src))
                print("---------------------------------------------------------")
            end
        end
    else
        print("No PROFINET packets found.")
    end
    
    file:close()
end

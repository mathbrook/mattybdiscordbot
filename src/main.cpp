#include <dpp/dpp.h>
#include <algorithm>
#include <vector>
#include <fstream>
#include <nlohmann/json.hpp>  // Include the JSON library

using json = nlohmann::json;

// Load bot token from bot_creds.json
std::string load_bot_token() {
    std::ifstream file("bot_creds.json");
    json creds;
    file >> creds;
    return creds["bot_token"];
}

uint64_t find_channel_by_criteria(const dpp::guild& guild, const dpp::cluster& bot) {
    std::vector<dpp::channel> text_channels;

    for (auto& [id, channel] : guild.channels) {
        if (channel.type == dpp::CHANNEL_TEXT) {  // Only consider text channels
            text_channels.push_back(channel);
        }
    }

    // Sort by alphabetical order (or numerical order if using channel IDs)
    std::sort(text_channels.begin(), text_channels.end(), [](const dpp::channel& a, const dpp::channel& b) {
        return a.name < b.name;  // Alphabetical order by name
        // return a.id < b.id;    // Numerical order by ID
    });

    return text_channels.empty() ? 0 : text_channels.front().id;
}

int main() {
    std::string bot_token = load_bot_token();

    dpp::cluster bot(bot_token);

    bot.on_ready([&bot](const dpp::ready_t& event) {
        for (const auto& [guild_id, guild] : bot.guilds) {
            uint64_t channel_id = find_channel_by_criteria(guild, bot);
            if (channel_id) {
                std::thread([&bot, channel_id]() {
                    while (true) {
                        std::this_thread::sleep_for(std::chrono::hours(1));
                        bot.message_create(dpp::message(channel_id, "This is an hourly message!"));
                    }
                }).detach();
            }
        }
    });

    bot.start(false);
    return 0;
}
